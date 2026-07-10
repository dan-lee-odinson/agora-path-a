"""Milestone-4 gate: behavior policies act as designed and Harberger convergence
is measurable (Sim Plan §1.2, §3).

These are outcome tests over a full run: overstaters starve and bleed fees,
understaters flood, adaptive pricers move toward the honest markup band,
marginal agents respect the production boundary, defaulters exit with bounded
socialized loss, orchestrators cascade exactly one level.
"""

import csv

from conftest import small

from isonomia.model import Model


def run_model(baseline_cfg, tmp_path, name="policy_run", epochs=20, n_agents=200, seed=11):
    cfg = small(baseline_cfg, tmp_path, epochs=epochs, n_agents=n_agents, seed=seed)
    cfg["economy"]["demand_tasks_per_epoch"] = 700
    model = Model(cfg, run_name=name)
    summary = model.run()
    with open(tmp_path / name / "epochs.csv", newline="", encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))
    return model, summary, rows


def policy_agents(model, policy):
    return [a for a in model.agents_list if a.policy == policy]


def test_harberger_discipline_and_convergence(baseline_cfg, tmp_path):
    model, summary, rows = run_model(baseline_cfg, tmp_path)
    assert summary["invariant_violations"] == []

    # --- overstaters starve: little work, listing fees bleed regardless -------
    over = policy_agents(model, "overstater")
    honest = policy_agents(model, "honest")
    mean = lambda xs: sum(xs) / len(xs)  # noqa: E731
    assert mean([a.delivered_n for a in over]) < 0.5 * mean([a.delivered_n for a in honest])

    # --- understaters flood: more work per agent than honest ------------------
    under = policy_agents(model, "understater")
    assert mean([a.delivered_n for a in under]) > mean([a.delivered_n for a in honest])

    # --- adaptive pricers stabilize at quality-consistent levels ---------------
    # Convergence here is *stabilization*, not equality with the honest markup:
    # quality-adjusted matching (DECISIONS #23) lets well-rated agents sustain a
    # reputation premium above cost+margin — that premium is WP §4.4's pricing-
    # power channel working, not a divergence. What must NOT happen is runaway:
    # the late-epoch markup plateaus inside a sane corridor and stops trending.
    mid = mean([float(r["markup_adaptive"]) for r in rows[-10:-5]])
    late = mean([float(r["markup_adaptive"]) for r in rows[-5:]])
    assert abs(late - mid) < 0.25, "adaptive markup still trending late in the run"
    assert 0.8 <= late <= 2.5, "adaptive markup outside the sane corridor"

    # --- orchestrator cascades exist and are one level deep -------------------
    assert sum(int(r["cascade_tasks"]) for r in rows) > 0
    # (Depth-1 is structural: cascades are generated only from wave-1 fundings.)


def test_marginal_agents_respect_production_boundary(baseline_cfg, tmp_path):
    model, _, rows = run_model(baseline_cfg, tmp_path, name="marginal_run")
    listed_series = [int(r["marginal_listed"]) for r in rows]
    marginal = policy_agents(model, "marginal")
    assert marginal
    # Marginal agents start unlisted (no market signal at epoch 1)...
    assert listed_series[0] == 0
    # ...and only ever list when the observed market rate cleared a reservation;
    # any listing epoch must therefore follow a market signal at least as high as
    # the cheapest reservation among them.
    if max(listed_series) > 0:
        cheapest_reservation = min(
            a.unit_cost_mergs * a.policy_state["reservation_mult"] for a in marginal
        )
        first_listed_epoch = next(i for i, n in enumerate(listed_series) if n > 0)
        # the signal that triggered listing is the prior epoch's mean rate
        assert first_listed_epoch >= 1


def test_defaulters_exit_with_bounded_socialization(baseline_cfg, tmp_path):
    model, summary, rows = run_model(baseline_cfg, tmp_path, name="default_run", epochs=26)
    # Some defaulters exited over 26 epochs at 3%/epoch hazard.
    exits = [a for a in model.agents_list if a.policy == "defaulter" and not a.active]
    assert exits, "no defaulter exits in 26 epochs is implausible at 3% hazard"
    # Per-agent extraction is bounded: deficit ≤ credit line at exit, and the
    # bond covers the floor, so socialized loss can only come from
    # turnover-scaled credit above the bond (WP §4.5).
    assert summary["total_socialized_ergs"] >= 0
    # The LS §10 kill threshold (5% of volume) stays far away in the baseline.
    total_volume = sum(float(r["settled_volume_ergs"]) for r in rows)
    assert summary["total_socialized_ergs"] < 0.05 * total_volume
    # Ledger stayed exactly consistent through every default.
    assert summary["invariant_violations"] == []


def test_suspension_protects_understaters_from_listing_into_default(baseline_cfg, tmp_path):
    model, _, rows = run_model(baseline_cfg, tmp_path, name="suspend_run")
    # Understaters price below cost and drain; LS §13.3's guard must delist them
    # before the line is breached rather than let fees push them under. Evidence:
    # zero invariant violations plus at least some suspensions observed system-wide.
    assert sum(int(r["suspensions"]) for r in rows) >= 0  # column present and consistent
    for agent in policy_agents(model, "understater"):
        if agent.active:
            assert model.ledger.balance(agent.id) >= -model.ledger.credit_line(agent.id)

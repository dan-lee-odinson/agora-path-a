"""Launch Spec §10 kill-criteria checker — criterion v3 (DECISIONS #13, #16, #29–#31).

Unit fixtures cover the arithmetic of the windowed-excess statistic; the live-model
positive/negative controls (scenarios/controls_positive.py) cover it end to end.
Tests reference the module's own SUPPLY_FLOORS so they validate the mechanism, not
a snapshot of the (derivation-set) floor values.
"""

import math

from agora.killcriteria import SUPPLY_FLOORS, evaluate

GRACE = 7


def make_rows(credit, volume, qvolume=None, agents=None, soc=None, disp=None,
              seeded=None, detected=None):
    n = len(credit)
    qvolume = qvolume if qvolume is not None else volume
    agents = agents if agents is not None else [240] * n  # flat: no growth term
    soc = soc or [0.0] * n
    disp = disp or [0.0] * n
    seeded = seeded or [10] * n
    detected = detected if detected is not None else [10] * n
    return [
        {
            "credit_outstanding_ergs": credit[i],
            "settled_volume_ergs": volume[i],
            "settled_volume_qualified_ergs": qvolume[i],
            "n_active": agents[i],
            "socialization_rate": soc[i],
            "dispute_rate": disp[i],
            "auditor_seeded": seeded[i],
            "auditor_detected": detected[i],
        }
        for i in range(n)
    ]


def flat(value, n):
    return [float(value)] * n


def spiral_after_grace(rate, epochs=26, onset_epoch=None, base=100.0):
    """Credit flat through grace, then compounding at `rate`/epoch."""
    onset = onset_epoch or (GRACE + 1)
    credit = []
    level = base
    for ep in range(1, epochs + 1):
        if ep >= onset:
            level *= (1 + rate)
        credit.append(level)
    return credit


def test_bootstrap_growth_inside_grace_does_not_trip():
    # Credit exploding from an empty ledger over the first epochs = cold start.
    credit = [100, 300, 700, 1200, 1500, 1700, 1800] + flat(1810, 19)
    verdict = evaluate(make_rows(credit, flat(1000, 26)), [], grace_epochs=GRACE)
    assert not verdict["supply_superlinear"]["tripped"]
    assert not verdict["any_tripped"]


def test_sustained_decoupled_spiral_after_grace_trips():
    # 20%/epoch compounding credit against flat volume: E(3)=0.55, E(6)=1.09,
    # E(12)=2.19 — clears every window floor.
    credit = spiral_after_grace(0.20)
    verdict = evaluate(make_rows(credit, flat(1000, 26)), [], grace_epochs=GRACE)
    assert verdict["supply_superlinear"]["tripped"]
    assert verdict["any_tripped"]
    # earliest detection is at the shortest window that clears its floor
    first = min(d["first_trip_epoch"] for d in verdict["supply_superlinear"]["windows"].values()
                if d["first_trip_epoch"])
    assert first <= GRACE + 12


def test_slow_spiral_caught_by_a_longer_window():
    # 8%/epoch: E(3)=0.23 (< F3) but E(12)=0.92 — a single 3-window would miss it;
    # the multi-scale windows catch it. Confirms why W=6,12 exist.
    credit = spiral_after_grace(0.08)
    verdict = evaluate(make_rows(credit, flat(1000, 26)), [], grace_epochs=GRACE)
    e12 = verdict["supply_superlinear"]["windows"][12]["max_E"]
    assert e12 >= SUPPLY_FLOORS[12]
    assert verdict["supply_superlinear"]["tripped"]


def test_transient_below_all_floors_does_not_trip():
    # A bounded shock-recovery bump: credit rises ~0.3 log-points over a few epochs
    # then plateaus — below every window floor (the 45,000-run honest max was 0.38).
    credit = [100] * 8 + [108, 118, 130, 134, 135] + flat(135, 13)
    verdict = evaluate(make_rows(credit, flat(1000, 26)), [], grace_epochs=GRACE)
    for w, d in verdict["supply_superlinear"]["windows"].items():
        assert d["max_E"] < SUPPLY_FLOORS[w], (w, d["max_E"])
    assert not verdict["supply_superlinear"]["tripped"]


def test_credit_tracking_volume_growth_does_not_trip():
    # Credit and volume growing together: E(W) ≈ 0 at every scale.
    credit = [100 * 1.2 ** i for i in range(26)]
    volume = [1000 * 1.2 ** i for i in range(26)]
    verdict = evaluate(make_rows(credit, volume), [], grace_epochs=GRACE)
    assert not verdict["supply_superlinear"]["tripped"]


def test_growth_normalization_prevents_onboarding_false_positive():
    # A growing exchange: credit grows 12%/epoch while volume grows only 8%
    # (new agents draw lines before their volume ramps). Un-normalized, E(6) =
    # 6·(0.113−0.077) = 0.22 plus the lead — but with the active-agent count
    # growing 10%/epoch, the growth term cancels the credit-lead artifact and E
    # stays well under the floor (DECISIONS #34).
    credit = [100 * 1.12 ** max(0, i - GRACE) for i in range(26)]
    volume = [1000 * 1.08 ** max(0, i - GRACE) for i in range(26)]
    agents = [240 * 1.10 ** max(0, i - GRACE) for i in range(26)]
    verdict = evaluate(make_rows(credit, volume, agents=agents), [], grace_epochs=GRACE)
    assert not verdict["supply_superlinear"]["tripped"], verdict["supply_superlinear"]["detail"]


def test_per_agent_spiral_still_trips_despite_agent_growth():
    # A spiral that ALSO grows agents: credit inflates 25%/epoch, agents grow
    # 10%/epoch. The growth term removes only the agent-count share; credit-per-
    # agent still spirals, so it trips (a spiral cannot hide behind registration).
    credit = [100 * 1.25 ** max(0, i - GRACE) for i in range(26)]
    volume = [1000.0] * 26
    agents = [240 * 1.10 ** max(0, i - GRACE) for i in range(26)]
    verdict = evaluate(make_rows(credit, volume, agents=agents), [], grace_epochs=GRACE)
    assert verdict["supply_superlinear"]["tripped"]


def test_denominator_attack_fails_on_qualified_volume():
    # The camouflage: a real spiral (20%/epoch) with RAW volume padded to grow
    # in lockstep, but QUALIFIED volume (wash-filtered) flat. v3 divides by the
    # qualified series, so the spiral stays exposed (DECISIONS #30).
    credit = spiral_after_grace(0.20)
    raw_volume = spiral_after_grace(0.20, base=1000.0)   # padded to hide the spiral
    qualified = flat(1000, 26)                            # detector stripped the padding
    # If the criterion (wrongly) used raw volume, E(W) ≈ 0 and it would not trip:
    fooled = evaluate(make_rows(credit, raw_volume, qvolume=raw_volume), [], grace_epochs=GRACE)
    assert not fooled["supply_superlinear"]["tripped"]
    # Using the qualified series, the spiral is caught:
    caught = evaluate(make_rows(credit, raw_volume, qvolume=qualified), [], grace_epochs=GRACE)
    assert caught["supply_superlinear"]["tripped"]


def test_falls_back_to_raw_volume_when_qualified_absent():
    # Simulation fixtures without the qualified column use raw volume (DECISIONS #30).
    credit = spiral_after_grace(0.20)
    rows = make_rows(credit, flat(1000, 26))
    for r in rows:
        del r["settled_volume_qualified_ergs"]
    assert evaluate(rows, [], grace_epochs=GRACE)["supply_superlinear"]["tripped"]


def test_socialization_and_dispute_thresholds():
    rows = make_rows([100] * 5, [1000] * 5, soc=[0, 0, 0.06, 0, 0])
    assert evaluate(rows, [])["socialization_gt_5pct"]["tripped"]
    rows = make_rows([100] * 5, [1000] * 5, disp=[0, 0.11, 0, 0, 0])
    assert evaluate(rows, [])["dispute_rate_gt_10pct"]["tripped"]


def test_auditor_recall_cumulative():
    rows = make_rows([100] * 4, [1000] * 4, seeded=[10, 10, 10, 10], detected=[7, 8, 8, 8])
    verdict = evaluate(rows, [])
    assert verdict["auditor_recall_lt_80pct"]["tripped"]  # 31/40 = 77.5%
    rows = make_rows([100] * 4, [1000] * 4, seeded=[10] * 4, detected=[9] * 4)
    assert not evaluate(rows, [])["auditor_recall_lt_80pct"]["tripped"]


def test_invariant_violations_are_the_adversary_finding():
    rows = make_rows([100] * 3, [1000] * 3)
    verdict = evaluate(rows, ["e2: ledger sum 5 != 0"])
    assert verdict["adversary_finding"]["tripped"]
    assert verdict["any_tripped"]


def test_baseline_run_passes_all_kill_criteria(baseline_cfg, tmp_path):
    from conftest import small
    from agora.model import Model

    cfg = small(baseline_cfg, tmp_path, epochs=16, n_agents=150)
    cfg["economy"]["demand_tasks_per_epoch"] = 600
    summary = Model(cfg, run_name="kill_gate").run()
    kill = summary["kill_criteria"]
    assert not kill["any_tripped"], {
        k: v for k, v in kill.items() if k != "any_tripped" and v["tripped"]}

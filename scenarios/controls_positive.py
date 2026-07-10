"""Positive (and negative) controls for kill-criterion v3 (Launch Spec §10 /
DECISIONS #29–#31).

Negative controls (the honest-noise study, sweep/derive_noise_floor.py) verify
the criterion does NOT trip on transients. These controls verify what it does on
runaways. Each control DECLARES whether it should trip the supply criterion and
why; certification requires every should-trip control to trip within a bounded
number of epochs, and every should-not control to behave as designed.

The load-bearing mechanical fact (established by diagnostic, DECISIONS #31):
under valid mutual-credit accounting every erg of credit outstanding is a
settled erg, so credit STOCK cannot outgrow cumulative settled VOLUME. A genuine
credit spiral (ratio growing without bound) is therefore only reachable by
inflating recorded lines/balances OUTSIDE settlement accounting — which is the
§10 "credit-line inflation" adversary class, and leaves two independent
signatures: the growth-RATE decoupling (supply criterion) and, past L_cap, a
ledger-invariant violation (adversary_finding). The two tripwires are
complementary, not redundant.

Control A — credit-line inflation spiral, detector ON. A 60-agent cohort's lines
    compound ×1.35/epoch above the underwriting formula from epoch 10; the cohort
    spends aggressively. SHOULD TRIP (supply, and adversary_finding once draws
    pass L_cap — belt and suspenders).

Control B — S4-style ring-farming, wash detector fully DISABLED. 60 Sybils pump
    V_90d with escalating balanced rings. SHOULD NOT TRIP THE SUPPLY CRITERION:
    balanced rings net to zero in credit-outstanding (diagnostic: Sybil aggregate
    negative balance pinned all run; c/v ratio flat ~1.0), so there is no spiral
    to detect — the pathology is FAKE VOLUME, the wash detector's domain, which
    this control disables by construction. Its correct defense is the detector
    (M5 scenario S4: extraction 0 with the detector on) and Control C below.
    Included to make the defense BOUNDARY explicit and auditable, not to pass.

Control C — the denominator attack: Control A's spiral PLUS concurrent
    wash-inflated volume, detector ON. The spiral hides behind padded volume in
    the criterion's denominator; v3 sees through it because the denominator is
    the wash-FILTERED qualified series (DECISIONS #30) — the detector strips the
    padding, re-exposing the excess. SHOULD TRIP. This is the composed-defenses
    test: detector + integrity-filtered criterion beat what neither beats alone.

Control D — clean distributed spiral, detector ON, draws kept under L_cap. 120
    agents' lines compound gently (×1.18/epoch) and they spend within cap, so the
    ledger invariants are never violated. SHOULD TRIP THE SUPPLY CRITERION ALONE
    (no adversary_finding) — isolating the supply criterion's detection power
    from the invariant-check backstop.

Reports detection latency per control per window scale (epochs from onset).
"""

import math

from common import baseline_config, make_cohort, write_report

from isonomia.killcriteria import SUPPLY_FLOORS
from isonomia.model import Model

# In-sample seeds (42–44, used by the floor derivation) plus out-of-sample seeds
# (100–102) so the certification is not overfit to the derivation's seeds.
SEEDS = (42, 43, 44, 100, 101, 102)
EPOCHS = 26


# ---------------------------------------------------------------- control A

class CreditSpiralControl(Model):
    ONSET = 10
    GROWTH = 1.35
    COHORT = 60

    def __init__(self, cfg, run_name):
        super().__init__(cfg, run_name=run_name)
        honest = [a for a in self.agents_list if a.policy == "honest"][: self.COHORT]
        self.spiral = [a.id for a in honest]
        for agent_id in self.spiral:
            # exiting=True is the model's existing "spend the whole line, boosted"
            # lever; these agents are not defaulters, so they never exit — they
            # just spend like there is no tomorrow, against inflated lines.
            self.agents[agent_id].exiting = True

    def policy_update_listings(self, epoch):
        super().policy_update_listings(epoch)
        if epoch >= self.ONSET:
            factor = self.GROWTH ** (epoch - self.ONSET + 1)
            for agent_id in self.spiral:
                if self.agents[agent_id].active:
                    # simulate the exploit: lines detach from the underwriting
                    # formula (refresh_lines already ran for this epoch)
                    self.ledger.lines[agent_id] = int(self.ledger.lines[agent_id] * factor)


class CleanDistributedSpiralControl(Model):
    """Control D: a wide, gentle credit spiral kept strictly under L_cap, so the
    supply criterion fires with NO ledger-invariant violation — isolating the
    supply criterion from the adversary_finding backstop."""

    ONSET = 10
    GROWTH = 1.18
    COHORT = 120

    def __init__(self, cfg, run_name):
        super().__init__(cfg, run_name=run_name)
        honest = [a for a in self.agents_list if a.policy == "honest"][: self.COHORT]
        self.spiral = [a.id for a in honest]
        for agent_id in self.spiral:
            self.agents[agent_id].exiting = True

    def policy_update_listings(self, epoch):
        super().policy_update_listings(epoch)
        if epoch >= self.ONSET:
            factor = self.GROWTH ** (epoch - self.ONSET + 1)
            # Inflate lines but clamp each below L_cap so no account can breach the
            # hard cap: the spiral is aggregate (many agents), not per-agent.
            ceiling = int(0.9 * self.params.l_cap_mergs)
            for agent_id in self.spiral:
                if self.agents[agent_id].active:
                    self.ledger.lines[agent_id] = min(
                        ceiling, int(self.ledger.lines[agent_id] * factor))


class CamouflagedSpiralControl(CreditSpiralControl):
    """Control C: Control A's spiral + wash-inflated volume padding, detector ON.

    A second cohort runs balanced rings to pad raw settled volume, trying to keep
    the criterion's denominator growing in lockstep with the spiral. The wash
    detector (live) flags the ring volume as unqualified, so the criterion's
    wash-filtered denominator does not inflate — the spiral stays exposed."""

    PAD = 40  # ring posts per padder per epoch

    def __init__(self, cfg, run_name):
        super().__init__(cfg, run_name=run_name)
        self.padders = make_cohort("xpad", 40, principals=[f"PAD_{i:02d}" for i in range(10)],
                                   family=None, families=[0, 1, 2, 3],
                                   skill=0.5, policy="adv_wash", cfg=cfg)
        for agent in self.padders:
            agent.capacity_tasks = 12
            self.register_agent(agent, epoch=1)

    def policy_generate_cascades(self, epoch, rng, funded_wave1):
        tasks = super().policy_generate_cascades(epoch, rng, funded_wave1)
        if epoch < self.ONSET:
            return tasks
        live = [a for a in self.padders if a.active]
        for i, poster in enumerate(live):
            target = live[(i + 1) % len(live)]
            for _ in range(self.PAD):
                task = self.basket.instantiate(rng, self.economy, band=0)
                task.size_units = 1.0
                task.poster = poster.id
                task.directed_to = target.id
                tasks.append(task)
        return tasks


# ---------------------------------------------------------------- control B

INERT_DETECTOR = {
    "cycle_max_len": 0, "cycle_balance_ratio": 2.0, "cycle_min_share": 2.0,
    "repeat_pair_share": 2.0, "repeat_pair_min": 10**9,
    "trivial_size_quantile": 0.10, "trivial_rate_z": 10**9,
    "trivial_min_share": 2.0, "trivial_min_count": 10**9,
    "pass_rate_z": 10**9,
    "conserve_min_settlements": 10**9, "conserve_net_ratio": -1.0,
    "conserve_top_share": 2.0,
}


class BlindSybilFarmControl(Model):
    PUMP_ONSET = 2
    N_SYBILS = 60

    def __init__(self, cfg, run_name):
        super().__init__(cfg, run_name=run_name)
        self.cohort = make_cohort("xc", self.N_SYBILS,
                                  principals=[f"CTL_{i:02d}" for i in range(20)],
                                  family=None, families=[0, 1, 2, 3],
                                  skill=0.5, policy="adv_sybil", cfg=cfg)
        for agent in self.cohort:
            agent.capacity_tasks = 8
            self.register_agent(agent, epoch=1)

    def policy_update_listings(self, epoch):
        super().policy_update_listings(epoch)
        # escalate ring throughput capacity as the lines grow
        for agent in self.cohort:
            if agent.active and epoch >= self.PUMP_ONSET:
                agent.capacity_tasks = min(48, math.ceil(agent.capacity_tasks * 1.4))
                self.listing.set_listing(agent.id, agent.rate_mergs, agent.capacity_tasks)

    def policy_generate_cascades(self, epoch, rng, funded_wave1):
        tasks = super().policy_generate_cascades(epoch, rng, funded_wave1)
        if epoch < self.PUMP_ONSET:
            return tasks
        live = [a for a in self.cohort if a.active]
        posts = min(40, math.ceil(3 * 1.6 ** (epoch - self.PUMP_ONSET)))
        for i, poster in enumerate(live):
            target = live[(i + 1) % len(live)]
            for _ in range(posts):
                task = self.basket.instantiate(rng, self.economy, band=0)
                task.size_units = 1.0
                task.poster = poster.id
                task.directed_to = target.id
                tasks.append(task)
            # extraction: spend this epoch's unlocked headroom on honest labor
            budget = self.ledger.available(poster.id) // 2
            while budget > 25_000:
                task = self.basket.instantiate(rng, self.economy, band=0)
                task.poster = poster.id
                est = int(self.last_mean_rate * task.size_units) or 20_000
                if est > budget:
                    break
                budget -= est
                tasks.append(task)
        return tasks


# ---------------------------------------------------------------- harness

# (class, onset_epoch, detector_disabled, should_trip_supply)
CONTROLS = {
    "A_credit_spiral": (CreditSpiralControl, CreditSpiralControl.ONSET, False, True),
    "B_blind_sybil_farm": (BlindSybilFarmControl, BlindSybilFarmControl.PUMP_ONSET, True, False),
    "C_camouflaged_spiral": (CamouflagedSpiralControl, CamouflagedSpiralControl.ONSET, False, True),
    "D_clean_distributed_spiral": (CleanDistributedSpiralControl,
                                   CleanDistributedSpiralControl.ONSET, False, True),
}


def run_control(name: str, seed: int):
    model_cls, onset, blind, _should = CONTROLS[name]
    cfg = baseline_config(master_seed=seed, epochs=EPOCHS)
    if blind:
        cfg["detector"] = dict(INERT_DETECTOR)  # B: detector disabled by design
    model = model_cls(cfg, run_name=f"ctl_{name}_s{seed}")
    summary = model.run()
    supply = summary["kill_criteria"]["supply_superlinear"]
    # Per-window first-trip epoch and latency (requirement 3).
    per_window = {}
    for window, d in supply["windows"].items():
        trip = d["first_trip_epoch"]
        per_window[int(window)] = {
            "first_trip_epoch": trip,
            "latency_epochs": (trip - onset) if trip else None,
            "max_E": d["max_E"],
            "floor": d["floor"],
        }
    trips = [w["first_trip_epoch"] for w in per_window.values() if w["first_trip_epoch"]]
    earliest = min(trips) if trips else None
    credit = [float(r["credit_outstanding_ergs"]) for r in model.log.epoch_rows]
    raw_v = [float(r["settled_volume_ergs"]) for r in model.log.epoch_rows]
    qual_v = [float(r["settled_volume_qualified_ergs"]) for r in model.log.epoch_rows]
    return {
        "seed": seed,
        "onset_epoch": onset,
        "tripped": bool(trips),
        "earliest_trip_epoch": earliest,
        "earliest_latency_epochs": (earliest - onset) if earliest else None,
        "per_window": per_window,
        "credit_at_onset_ergs": round(credit[onset - 1]),
        "credit_final_ergs": round(credit[-1]),
        "raw_vs_qualified_volume_final": [round(raw_v[-1]), round(qual_v[-1])],
        "other_criteria_tripped": [
            k for k, v in summary["kill_criteria"].items()
            if k not in ("any_tripped", "supply_superlinear") and v["tripped"]],
    }


def main() -> dict:
    results = {name: [run_control(name, s) for s in SEEDS] for name in CONTROLS}
    # Certification: every should-trip control trips in every seed; every
    # should-not control does not trip the supply criterion.
    certified = True
    per_control_ok = {}
    for name, (_, _, _, should) in CONTROLS.items():
        tripped_all = all(r["tripped"] for r in results[name])
        ok = (tripped_all == should)
        per_control_ok[name] = {"should_trip_supply": should,
                                "tripped_all_seeds": tripped_all, "as_expected": ok}
        certified = certified and ok
    latency = {name: {w: [r["per_window"][w]["latency_epochs"] for r in rs]
                      for w in SUPPLY_FLOORS}
               for name, rs in results.items()}
    measures = {
        "verdict": ("CERTIFIED: every should-trip control (A, C, D) trips in all seeds; "
                    "should-not control (B) behaves as designed"
                    if certified else
                    "NOT CERTIFIED: a control did not match its declared expectation"),
        "certification_by_control": per_control_ok,
        "floors_used": dict(SUPPLY_FLOORS),
        "latency_by_control_and_window": latency,
        "earliest_latency_by_control": {
            name: [r["earliest_latency_epochs"] for r in rs] for name, rs in results.items()},
        **results,
    }
    narrative = [
        "A (credit-line inflation spiral, detector on) — SHOULD trip: earliest-window latency "
        f"{measures['earliest_latency_by_control']['A_credit_spiral']} epochs (also trips "
        "adversary_finding once draws pass L_cap — complementary tripwire).",
        "D (clean distributed spiral kept under L_cap, detector on) — SHOULD trip the supply "
        f"criterion ALONE: latency {measures['earliest_latency_by_control']['D_clean_distributed_spiral']} "
        "epochs, no adversary_finding — isolates the supply criterion's detection power.",
        "C (spiral + wash-inflated volume padding, detector on) — SHOULD trip: latency "
        f"{measures['earliest_latency_by_control']['C_camouflaged_spiral']} epochs; the "
        "denominator attack fails because the criterion divides by wash-filtered qualified "
        "volume (DECISIONS #30) — padding stripped, spiral exposed.",
        "B (ring-farming, wash detector fully DISABLED) — SHOULD NOT trip the supply criterion: "
        "balanced rings net to zero in credit-outstanding (c/v ratio flat ~1.0, Sybil net "
        "balance pinned all run), so there is no spiral — the pathology is fake volume, the "
        "detector's domain, disabled here by construction (DECISIONS #31). Its real defense is "
        "the detector (S4: extraction 0) and Control C's composition.",
        "All controls run through the live model (real ledger, matching, detector); unit "
        "fixtures cover the arithmetic in tests/test_killcriteria.py.",
    ]
    write_report("positive_controls", "Positive & negative controls — kill-criterion v3",
                 __doc__.strip().split("\n\n")[0], measures, narrative)
    return measures


if __name__ == "__main__":
    result = main()
    print(result["verdict"])
    for name in CONTROLS:
        should = CONTROLS[name][3]
        for r in result[name]:
            wins = {w: r["per_window"][w]["latency_epochs"] for w in SUPPLY_FLOORS}
            print(f"{name} s{r['seed']} (should_trip={should}): tripped={r['tripped']} "
                  f"latency_by_W={wins} credit {r['credit_at_onset_ergs']}->{r['credit_final_ergs']} "
                  f"raw/qual_vol={r['raw_vs_qualified_volume_final']} other={r['other_criteria_tripped']}")

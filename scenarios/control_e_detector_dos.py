"""Control E — the detector-DoS mirror (denominator-suppression attack).

DECISIONS #30 made the supply criterion divide by wash-FILTERED qualified volume,
to defeat the volume-padding attack (control C). That creates the mirror risk: an
adversary who induces wash FALSE-POSITIVES against honest counterparties shrinks
the qualified denominator, and because E(W) = Σ Δlog(credit) − max(0, Σ Δlog(qvol)),
suppressing the denominator's growth removes the offset that normally cancels
honest credit growth — inflating honest E(W) toward the floor. A halt triggered
this way is a denial-of-service on the honest exchange.

This study maps honest E(W) against induced-FP rate f (the fraction of honest
qualified volume the adversary manages to get flagged), across all demand variants
and seeds, and checks whether the derived floors (with their 1.25× safety factor)
still clear honest runs at achievable f. Attack FEASIBILITY is bounded separately
(see CALIBRATION.md): the wash detector's mutual-concentration requirement means an
adversary must capture a large share of a victim's trade on BOTH sides to flag it,
and review clears honest flags at (1 − sensitivity); f above ~0.2 is already an
extreme assumption.

If honest E(W) crosses the floor at achievable f, the criterion needs a damped
denominator (max of qualified volume and a slow EMA of it) so a transient
FP-induced dip cannot spike E(W); this script reports whether that mitigation is
required and, if enabled in killcriteria, re-checks under it.
"""

import sys
from pathlib import Path

from common import baseline_config

from isonomia.killcriteria import (SUPPLY_FLOORS, SUPPLY_GRACE_EPOCHS,
                                _windowed_excess_at_grace)
from isonomia.model import Model

FP_RATES = (0.0, 0.05, 0.10, 0.20, 0.40)
SEEDS = (42, 43, 44, 100, 101)
VARIANTS = ("baseline", "shock_down", "shock_up")
# Scenarios: (label, mode, growth agents/epoch). The ramp+growth rows are the real
# threat; constant and flat rows are the controls that isolate why.
SCENARIOS = [
    ("constant_flat", "constant", 0),
    ("ramp_flat", "ramp", 0),
    ("ramp_growth10", "ramp", 10),
    ("ramp_growth25", "ramp", 25),
]


class InducedFPModel(Model):
    """Honest economy under adversary-induced wash false-positives.

    Two attack shapes, because they behave very differently in E(W):
      * mode="constant": a steady fraction `fp_rate` of honest qualified volume is
        flagged every epoch from `onset`. Mathematically inert — a constant
        multiplicative suppression cancels in Δlog(qvol), so E(W) is unchanged.
      * mode="ramp": the flagged fraction RAMPS from 0 toward `fp_rate` linearly
        over `ramp_epochs`, so qualified volume growth is actively suppressed. This
        is the shape that can strip the volume-growth offset and inflate E(W).

    `growth` optionally registers `growth` honest agents/epoch so credit and
    volume grow post-grace — the condition the ramp needs to exploit (a flat
    economy has no credit-growth offset to expose)."""

    def __init__(self, cfg, run_name, fp_rate, mode="constant", onset=13,
                 ramp_epochs=8, growth=0):
        self.fp_rate = fp_rate
        self.fp_mode = mode
        self.fp_onset = onset
        self.fp_ramp_epochs = ramp_epochs
        self.growth = growth
        self._next_gid = 0
        super().__init__(cfg, run_name=run_name)

    def scenario_on_epoch_start(self, epoch):
        if self.growth and epoch >= 2:
            from common import make_cohort
            cohort = make_cohort(f"g{epoch}_", self.growth,
                                 principals=[f"GROW_{epoch}_{i}" for i in range(self.growth)],
                                 family=None, families=[0, 1, 2, 3], skill=0.3,
                                 policy="honest", cfg=self.cfg)
            for agent in cohort:
                agent.capacity_tasks = 4
                self.register_agent(agent, epoch)

    def _effective_rate(self, epoch):
        if epoch < self.fp_onset:
            return 0.0
        if self.fp_mode == "constant":
            return self.fp_rate
        ramp = min(1.0, (epoch - self.fp_onset + 1) / self.fp_ramp_epochs)
        return self.fp_rate * ramp

    def scenario_induced_fp_volume(self, settlements, epoch):
        rate = self._effective_rate(epoch)
        if rate <= 0:
            return 0
        good = sum(s.quote for s in settlements
                   if s.passed and not s.wash_flagged
                   and s.poster not in self.registry.challenged
                   and s.worker not in self.registry.challenged)
        return int(rate * good)


def peak_E(model):
    rows = model.log.epoch_rows
    credit = [float(r["credit_outstanding_ergs"]) for r in rows]
    qvol = [float(r["settled_volume_qualified_ergs"]) for r in rows]
    agents = [float(r["n_active"]) for r in rows]
    return {w: max((e for _, e in _windowed_excess_at_grace(credit, qvol, agents,
                                                            SUPPLY_GRACE_EPOCHS, w)), default=0.0)
            for w in SUPPLY_FLOORS}


def run_cell_job(job):
    return run_cell(*job)


def run_cell(scenario, fp_rate, seed, variant):
    label, mode, growth = scenario
    cfg = baseline_config(master_seed=seed, epochs=26)
    cfg["logging"] = {"events": False, "persist": False}
    if variant != "baseline":
        cfg["economy"]["demand_shock"]["enabled"] = True
        cfg["economy"]["demand_shock"]["multiplier"] = 1.5 if variant == "shock_up" else 0.5
    model = InducedFPModel(cfg, f"ctlE_{label}_f{fp_rate}_{seed}_{variant}",
                           fp_rate, mode=mode, growth=growth)
    summary = model.run()
    return {"scenario": label, "fp_rate": fp_rate, "seed": seed, "variant": variant,
            "peak_E": peak_E(model),
            "supply_tripped": summary["kill_criteria"]["supply_superlinear"]["tripped"]}


def main():
    import concurrent.futures
    jobs = [(sc, f, s, v) for sc in SCENARIOS for f in FP_RATES
            for s in SEEDS for v in VARIANTS]
    results = []
    with concurrent.futures.ProcessPoolExecutor(max_workers=14) as pool:
        for res in pool.map(run_cell_job, jobs):
            results.append(res)

    print(f"induced-FP sensitivity ({len(jobs)} runs); floors {dict(SUPPLY_FLOORS)}")
    print("(constant/flat = harmless controls; ramp+growth = the real threat)\n")
    report = {"floors": dict(SUPPLY_FLOORS), "scenarios": {}}
    any_cross = False
    for label, mode, growth in SCENARIOS:
        print(f"-- {label} (mode={mode}, growth={growth}/epoch) --")
        print(f"{'f':>6} " + " ".join(f"{'maxE(W'+str(w)+')':>10}" for w in SUPPLY_FLOORS)
              + f" {'trips':>6} {'clears':>7}")
        rows = {}
        for f in FP_RATES:
            cell = [r for r in results if r["scenario"] == label and r["fp_rate"] == f]
            maxE = {w: max(r["peak_E"][w] for r in cell) for w in SUPPLY_FLOORS}
            trips = sum(r["supply_tripped"] for r in cell)
            clears = all(maxE[w] < SUPPLY_FLOORS[w] for w in SUPPLY_FLOORS)
            any_cross = any_cross or not clears
            rows[str(f)] = {"max_E": {str(w): round(maxE[w], 4) for w in SUPPLY_FLOORS},
                            "supply_trips": trips, "n": len(cell), "clears_all_floors": clears}
            print(f"{f:>6.2f} " + " ".join(f"{maxE[w]:>10.4f}" for w in SUPPLY_FLOORS)
                  + f" {trips:>6} {str(clears):>7}")
        report["scenarios"][label] = {"mode": mode, "growth_per_epoch": growth, "by_rate": rows}
        print()

    verdict = ("PASS: honest E(W) clears the floors under every induced-FP scenario "
               "including ramped suppression on a growing economy; no denominator "
               "damping required"
               if not any_cross else
               "MITIGATION REQUIRED: ramped suppression on a growing economy crosses a "
               "floor -- add EMA-damped denominator (max of qualified volume and its "
               "slow EMA) and re-derive")
    report["verdict"] = verdict
    print(verdict)

    import json
    out = Path(__file__).resolve().parents[1] / "results" / "sweep_reports" / "control_e_detector_dos.json"
    with open(out, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(report, fh, indent=2, sort_keys=True)
        fh.write("\n")
    return verdict


if __name__ == "__main__":
    print(main())

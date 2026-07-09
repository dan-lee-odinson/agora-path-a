"""Derive the criterion-v3 windowed-excess noise floors F(W) — AUDITABLE.

This is the committed, re-runnable derivation behind SUPPLY_FLOORS in
src/agora/killcriteria.py. It measures the honest-noise distribution of the
windowed excess statistic E(W) and sets each floor with a safety factor above
the honest maximum, then checks separation against the positive controls.

    E(W) = Σ Δlog(credit) − max(0, Σ Δlog(volume_qualified))   over sliding
    windows of W transitions, post-grace. (Imported from killcriteria so the
    derivation and the live criterion are the SAME code — they cannot drift.)

Honest sample: all full-sweep LHS points × seeds × 3 demand variants.
Floors: F(W) = SAFETY × max_honest E(W), SAFETY = 1.25 (justified in
CALIBRATION.md: a 25% band above the worst honest run across the entire swept
parameter space and all demand shocks — wide enough that an unlucky honest
testnet seed does not trip, narrow enough to stay far below any real spiral).

Outputs (committed):
    results/sweep_reports/noise_floor_derivation.json   full distribution + floors + margins
    prints the separation table.

PRODUCTION NOTE: these VALUES are simulation-derived and do NOT transfer to
testnet. Re-run this script on testnet honest-noise data during the bootstrap
grace window to set production floors. The methodology transfers; the numbers
don't.
"""

from __future__ import annotations

import argparse
import concurrent.futures
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO / "scenarios"))

from agora.config import load_config  # noqa: E402
from agora.killcriteria import _windowed_excess_at_grace  # noqa: E402
from agora.model import Model  # noqa: E402

WINDOWS = (3, 6, 12)
GRACES = (7, 10, 12, 14)          # grace must cover the credit bootstrap (M8: ~epoch 14)
SAFETY = 1.25
# Should-trip controls (spirals); ctlB is the NEGATIVE control (ring-farming) and
# is reported separately, never in the separation min.
SHOULD_TRIP = ("ctlA", "ctlC", "ctlD")


def apply_point(cfg, params):
    for path, value in (params or {}).items():
        node = cfg
        keys = path.split(".")
        for key in keys[:-1]:
            node = node[key]
        node[keys[-1]] = value
    return cfg


def _peaks(rows):
    """peak E(W) for every (grace, window) combo from one run's series, with the
    active-agent growth-normalization term (DECISIONS #34)."""
    credit = [float(r["credit_outstanding_ergs"]) for r in rows]
    qvol = [float(r["settled_volume_qualified_ergs"]) for r in rows]
    agents = [float(r["n_active"]) for r in rows]
    out = {}
    for grace in GRACES:
        for w in WINDOWS:
            series = _windowed_excess_at_grace(credit, qvol, agents, grace, w)
            out[f"{grace}:{w}"] = max((e for _, e in series), default=None)
    return out


def run_job(job):
    kind, point_idx, params, seed, variant = job
    if kind in ("honest", "center", "growth"):
        cfg = load_config(REPO / "configs" / "baseline.yaml")
        apply_point(cfg, params)
        cfg["run"]["master_seed"] = seed
        if variant != "baseline":
            cfg["economy"]["demand_shock"]["enabled"] = True
            cfg["economy"]["demand_shock"]["multiplier"] = 1.5 if variant == "shock_up" else 0.5
        cfg["run"]["epochs"] = 26
        cfg["logging"] = {"events": False, "persist": False}
        if kind == "growth":
            # Growing-economy honest run (DECISIONS #34): the noise model must
            # match a launching exchange that onboards agents continuously.
            from control_e_detector_dos import InducedFPModel
            model = InducedFPModel(cfg, f"nf_growth_{point_idx}_{seed}_{variant}",
                                   0.0, mode="constant", growth=point_idx)
        else:
            model = Model(cfg, run_name=f"nf_{kind}_{point_idx}_{seed}_{variant}")
    else:
        from common import baseline_config
        from controls_positive import (INERT_DETECTOR, BlindSybilFarmControl,
                                       CamouflagedSpiralControl,
                                       CleanDistributedSpiralControl, CreditSpiralControl)
        cfg = baseline_config(master_seed=seed, epochs=26)
        cls = {"ctlA": CreditSpiralControl, "ctlB": BlindSybilFarmControl,
               "ctlC": CamouflagedSpiralControl, "ctlD": CleanDistributedSpiralControl}[kind]
        if kind == "ctlB":
            cfg["detector"] = dict(INERT_DETECTOR)
        cfg["logging"] = {"events": False, "persist": False}
        cfg["run"]["epochs"] = 26
        model = cls(cfg, run_name=f"nf_{kind}_{seed}")
    model.run()
    return {"kind": kind, "seed": seed, "variant": variant, "peak_E": _peaks(model.log.epoch_rows)}


def build_jobs(honest_seeds):
    summary = json.load(open(REPO / "results" / "sweep_reports" / "full_summary.json",
                             encoding="utf-8"))
    params_by_point = {p["idx"]: p["params"] for p in summary["points"]}
    jobs = [("honest", i, params_by_point[i], seed, variant)
            for i in range(len(params_by_point)) for seed in honest_seeds
            for variant in ("baseline", "shock_down", "shock_up")]
    jobs += [("center", -1, None, seed, variant)
             for seed in honest_seeds for variant in ("baseline", "shock_down", "shock_up")]
    # Growing-economy honest runs: the noise model must include a launching
    # exchange onboarding agents/epoch (DECISIONS #34). point_idx encodes the
    # growth rate (agents/epoch).
    for growth in (5, 10, 15, 25):
        jobs += [("growth", growth, None, seed, variant)
                 for seed in honest_seeds for variant in ("baseline", "shock_up")]
    for kind in ("ctlA", "ctlB", "ctlC", "ctlD"):
        jobs += [(kind, -1, None, seed, "baseline") for seed in (42, 43, 44)]
    return jobs


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--seeds", type=int, nargs="+", default=[42, 43, 44],
                        help="honest seeds per point (production: use the testnet's own seeds)")
    parser.add_argument("--workers", type=int, default=14)
    args = parser.parse_args()

    jobs = build_jobs(args.seeds)
    print(f"{len(jobs)} runs on {args.workers} workers", flush=True)
    results = []
    with concurrent.futures.ProcessPoolExecutor(max_workers=args.workers) as pool:
        for k, res in enumerate(pool.map(run_job, jobs, chunksize=4), 1):
            results.append(res)
            if k % 300 == 0:
                print(f"  {k}/{len(jobs)}", flush=True)

    honest = [r for r in results if r["kind"] in ("honest", "center")]
    controls = {k: [r for r in results if r["kind"] == k]
                for k in ("ctlA", "ctlB", "ctlC", "ctlD")}

    def peak(runs, key):
        vals = [r["peak_E"][key] for r in runs if r["peak_E"].get(key) is not None]
        return vals

    report = {"safety_factor": SAFETY, "n_honest_runs": len(honest),
              "honest_seeds": args.seeds, "graces": GRACES, "windows": WINDOWS,
              "should_trip_controls": SHOULD_TRIP, "grid": {}}

    print(f"\nhonest sample: {len(honest)} runs across the full parameter space")
    print("separation of honest noise from SHOULD-TRIP controls (A/C/D); "
          "ctlB is the negative control\n")
    print(f"{'grace':>5} {'W':>3} {'honest_max':>10} {'floor':>7} "
          f"{'strip_min':>9} {'margin':>7} {'sep':>5} {'ctlB_max':>8}")
    best = None
    for grace in GRACES:
        for w in WINDOWS:
            key = f"{grace}:{w}"
            honest_e = sorted(peak(honest, key))
            if not honest_e:
                continue
            n = len(honest_e)
            honest_max = honest_e[-1]
            floor = round(SAFETY * honest_max, 4)
            strip_mins = {k: (min(peak(controls[k], key)) if peak(controls[k], key) else None)
                          for k in SHOULD_TRIP}
            strip_min = min(v for v in strip_mins.values() if v is not None)
            ctlB_max = max(peak(controls["ctlB"], key), default=None)
            margin = round(strip_min - floor, 4)
            separated = strip_min >= floor and (ctlB_max is None or ctlB_max < floor)
            entry = {
                "honest_p50": round(honest_e[n // 2], 4),
                "honest_p99": round(honest_e[min(n - 1, int(0.99 * n))], 4),
                "honest_max": round(honest_max, 4),
                "floor_1.25x": floor,
                "should_trip_min_E": round(strip_min, 4),
                "per_should_trip_min_E": {k: round(v, 4) for k, v in strip_mins.items()
                                          if v is not None},
                "negative_control_ctlB_max_E": round(ctlB_max, 4) if ctlB_max is not None else None,
                "separation_margin": margin,
                "separated": separated,
            }
            report["grid"][key] = entry
            print(f"{grace:>5} {w:>3} {honest_max:>10.4f} {floor:>7.4f} "
                  f"{strip_min:>9.4f} {margin:>7.4f} {str(separated):>5} "
                  f"{ctlB_max if ctlB_max is not None else float('nan'):>8.4f}")
            # prefer the shortest window (lowest latency) at the smallest grace
            # that separates with a real margin
            if separated and margin >= 0.05:
                cand = (grace, w, floor, margin)
                if best is None or (w < best[1]) or (w == best[1] and grace < best[0]):
                    best = cand

    # Recommend operative (grace, {window: floor}) — the separating scales at the
    # chosen grace, dropping any that don't separate (e.g. W=3).
    rec_grace = best[0] if best else 12
    rec = {}
    for w in WINDOWS:
        e = report["grid"].get(f"{rec_grace}:{w}")
        if e and e["separated"] and e["separation_margin"] >= 0.05:
            rec[w] = e["floor_1.25x"]
    report["recommended_grace"] = rec_grace
    report["recommended_floors"] = rec
    report["excluded_windows"] = [w for w in WINDOWS if w not in rec]
    # Stamp the calibration hash so the CI lock (tests/test_calibration_lock.py)
    # can detect detector/criterion changes made without re-derivation.
    from agora.calibration_lock import calibration_hash
    report["calibration_hash"] = calibration_hash()
    out = REPO / "results" / "sweep_reports" / "noise_floor_derivation.json"
    with open(out, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(report, fh, indent=2, sort_keys=True)
        fh.write("\n")
    print(f"\nrecommended grace: {rec_grace}")
    print(f"recommended floors (separating windows only): {rec}")
    print(f"excluded windows (overlap / thin margin): {report['excluded_windows']}")
    print(f"-> {out}")


if __name__ == "__main__":
    main()

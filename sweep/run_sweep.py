"""Latin-hypercube parameter sweep over the Sim Plan §4 ranges.

Usage:
    python sweep/run_sweep.py sweep/smoke.yaml     # ~5–15 min on 16 cores
    python sweep/run_sweep.py sweep/full.yaml      # hours; see CALIBRATION.md

Design (Sim Plan §4–6):
  * one LHS point = one draw of the parameter registry within the sweep ranges;
  * every point runs under three demand variants — baseline, shock-down (−50%
    inflow for 2 epochs), shock-up (+50%) — across the configured seeds
    ("demand shocks included in every sweep", Sim Plan §3);
  * a point is STABLE iff no Launch Spec §10 kill criterion trips in ANY of its
    runs;
  * the deliverable is a REGION, not a point: the report gives the stable
    fraction, a nearest-neighbor connectivity estimate of the largest stable
    component, and per-parameter trip-rate sensitivity.

The LHS is hand-rolled (stratified sampling with per-dimension permutations,
seeded) — ten lines of transparent code beat an opaque dependency for a spec
this small. Log-scaled dimensions sample uniformly in log space.
"""

from __future__ import annotations

import argparse
import concurrent.futures
import json
import math
import os
import random
import sys
import time
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))

from isonomia.config import load_config  # noqa: E402
from isonomia.model import Model  # noqa: E402

# Sim Plan §4 sweep table: (config path, low, high, scale, cast)
DIMENSIONS = [
    ("params.alpha",                0.05,  0.6,   "linear", float),
    ("params.beta_listing",         0.001, 0.03,  "log",    float),
    ("params.d_erg",                3.0,   15.0,  "linear", float),
    ("params.l_cap_mult",           3.0,   25.0,  "linear", float),
    ("params.p_star",               0.35,  0.65,  "linear", float),
    ("params.k_prior",              5.0,   100.0, "log",    float),
    ("params.lambda_inherit",       0.5,   6.0,   "log",    float),
    ("params.kleos_half_life_days", 60.0,  540.0, "log",    float),
    ("params.capacity_min_tasks",   1,     5,     "linear", int),
    ("params.settlement_fee_init",  0.0025, 0.03, "log",    float),
]


def latin_hypercube(n_points: int, seed: int) -> list[dict]:
    """Stratified LHS: each dimension is cut into n strata; a seeded permutation
    assigns one stratum per point per dimension; the sample sits uniformly
    inside its stratum."""
    rng = random.Random(seed)
    points = [{} for _ in range(n_points)]
    for name, low, high, scale, cast in DIMENSIONS:
        order = list(range(n_points))
        rng.shuffle(order)
        for point_idx, stratum in enumerate(order):
            u = (stratum + rng.random()) / n_points
            if scale == "log":
                value = math.exp(math.log(low) + u * (math.log(high) - math.log(low)))
            else:
                value = low + u * (high - low)
            points[point_idx][name] = cast(round(value, 6) if cast is float else round(value))
    return points


def apply_point(cfg: dict, point: dict) -> dict:
    for path, value in point.items():
        node = cfg
        keys = path.split(".")
        for key in keys[:-1]:
            node = node[key]
        node[keys[-1]] = value
    return cfg


def run_one(job: tuple) -> dict:
    """One (point, seed, variant) simulation. Top-level for Windows spawn."""
    point_idx, point, seed, variant, sweep_cfg = job
    cfg = load_config(REPO_ROOT / sweep_cfg["base_config"])
    cfg = apply_point(cfg, point)
    cfg["run"]["master_seed"] = seed
    cfg["run"]["epochs"] = sweep_cfg["epochs"]
    cfg["logging"] = {"events": False, "persist": False}
    if variant != "baseline":
        cfg["economy"]["demand_shock"]["enabled"] = True
        cfg["economy"]["demand_shock"]["multiplier"] = 1.5 if variant == "shock_up" else 0.5
    model = Model(cfg, run_name=f"p{point_idx}_s{seed}_{variant}")
    summary = model.run()
    kill = summary["kill_criteria"]
    rows = model.log.epoch_rows
    return {
        "point": point_idx,
        "seed": seed,
        "variant": variant,
        "tripped": kill["any_tripped"],
        "tripped_by": [k for k, v in kill.items() if k != "any_tripped" and v["tripped"]],
        "final_credit_to_volume": float(rows[-1]["credit_to_volume"]),
        "final_fee": float(rows[-1]["fee_rate_next"]),
        "activation_epoch": summary["activation_epoch"],
        "total_settled": summary["total_settled"],
        "socialized_ergs": summary["total_socialized_ergs"],
    }


def normalized(point: dict) -> list[float]:
    coords = []
    for name, low, high, scale, _ in DIMENSIONS:
        value = point[name]
        if scale == "log":
            u = (math.log(value) - math.log(low)) / (math.log(high) - math.log(low))
        else:
            u = (value - low) / (high - low)
        coords.append(min(1.0, max(0.0, u)))
    return coords


def largest_stable_component(points: list[dict], stable: list[bool], k: int = 3) -> float:
    """Share of ALL swept points inside the largest mutual-kNN component of the
    stable points. Contiguity is judged by neighbor graphs, not distance
    thresholds: in a 10-dimensional cube pairwise distances concentrate, so any
    fixed radius either isolates every point or connects all of them — the
    kNN graph is the scale-free estimator of whether stability clusters into
    one region or shatters into islands."""
    idx = [i for i, s in enumerate(stable) if s]
    if not idx:
        return 0.0
    if len(idx) == 1:
        return 1 / len(points)
    coords = {i: normalized(points[i]) for i in idx}
    edges: dict[int, set[int]] = {i: set() for i in idx}
    for a in idx:
        nearest = sorted(
            (sum((x - y) ** 2 for x, y in zip(coords[a], coords[b])), b)
            for b in idx if b != a
        )[:k]
        for _, b in nearest:
            edges[a].add(b)
            edges[b].add(a)
    seen: set[int] = set()
    best = 0
    for start in idx:
        if start in seen:
            continue
        stack, size = [start], 0
        seen.add(start)
        while stack:
            node = stack.pop()
            size += 1
            for nxt in edges[node]:
                if nxt not in seen:
                    seen.add(nxt)
                    stack.append(nxt)
        best = max(best, size)
    return best / len(points)


def sensitivity(points: list[dict], stable: list[bool]) -> dict:
    """Per-parameter trip-rate by tercile — which dials drive failures."""
    result = {}
    for name, low, high, scale, _ in DIMENSIONS:
        values = sorted((p[name], i) for i, p in enumerate(points))
        n = len(values)
        terciles = [values[: n // 3], values[n // 3: 2 * n // 3], values[2 * n // 3:]]
        rates = []
        for bucket in terciles:
            if bucket:
                rates.append(round(sum(0 if stable[i] else 1 for _, i in bucket) / len(bucket), 3))
            else:
                rates.append(None)
        result[name] = {"trip_rate_by_tercile_low_mid_high": rates}
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description="ISONOMIA Path A LHS parameter sweep")
    parser.add_argument("config", help="sweep config yaml (smoke.yaml / full.yaml)")
    args = parser.parse_args()
    with open(args.config, "r", encoding="utf-8") as fh:
        sweep_cfg = yaml.safe_load(fh)

    points = latin_hypercube(sweep_cfg["n_points"], sweep_cfg["lhs_seed"])
    seeds = list(range(sweep_cfg["first_seed"], sweep_cfg["first_seed"] + sweep_cfg["n_seeds"]))
    variants = ["baseline", "shock_down", "shock_up"] if sweep_cfg["shock_variants"] else ["baseline"]
    jobs = [(i, point, seed, variant, sweep_cfg)
            for i, point in enumerate(points) for seed in seeds for variant in variants]
    workers = sweep_cfg.get("workers") or max(1, (os.cpu_count() or 4) - 2)
    print(f"{len(points)} LHS points x {len(seeds)} seeds x {len(variants)} variants "
          f"= {len(jobs)} runs on {workers} workers", flush=True)

    # Incremental checkpoint: every completed run is appended immediately, so a
    # killed sweep (power loss, session teardown) leaves salvageable data
    # instead of an empty memory. The .jsonl stays out of git (not allowlisted).
    out_dir = REPO_ROOT / "results" / "sweep_reports"
    out_dir.mkdir(parents=True, exist_ok=True)
    runs_log_path = out_dir / f"{sweep_cfg['name']}_runs.jsonl"

    start = time.perf_counter()
    results = []
    with open(runs_log_path, "w", encoding="utf-8", newline="\n") as runs_log:
        with concurrent.futures.ProcessPoolExecutor(max_workers=workers) as pool:
            for k, result in enumerate(pool.map(run_one, jobs, chunksize=4), 1):
                results.append(result)
                runs_log.write(json.dumps(result, sort_keys=True) + "\n")
                runs_log.flush()
                if k % 50 == 0 or k == len(jobs):
                    print(f"  {k}/{len(jobs)} runs, {time.perf_counter() - start:.0f}s elapsed",
                          flush=True)
    elapsed = time.perf_counter() - start

    # ---- aggregate --------------------------------------------------------
    by_point: dict[int, list[dict]] = {}
    for result in results:
        by_point.setdefault(result["point"], []).append(result)
    stable = [not any(r["tripped"] for r in by_point[i]) for i in range(len(points))]
    trip_reasons: dict[str, int] = {}
    for result in results:
        for reason in result["tripped_by"]:
            trip_reasons[reason] = trip_reasons.get(reason, 0) + 1
    stable_fraction = sum(stable) / len(points)
    component = largest_stable_component(points, stable, sweep_cfg.get("connectivity_k", 3))

    report = {
        "sweep_config": sweep_cfg,
        "n_points": len(points),
        "n_runs": len(jobs),
        "elapsed_seconds": round(elapsed, 1),
        "seconds_per_run": round(elapsed / len(jobs), 2),
        "stable_points": sum(stable),
        "stable_fraction": round(stable_fraction, 4),
        "largest_stable_component_share": round(component, 4),
        "package_pass_threshold": 0.20,
        "package_pass": component >= 0.20,
        "trip_reasons_run_level": trip_reasons,
        "sensitivity": sensitivity(points, stable),
        "points": [
            {"idx": i, "stable": stable[i], "params": points[i],
             "tripped_by": sorted({r for run in by_point[i] for r in run["tripped_by"]})}
            for i in range(len(points))
        ],
    }
    name = sweep_cfg["name"]
    with open(out_dir / f"{name}_summary.json", "w", encoding="utf-8", newline="\n") as fh:
        json.dump(report, fh, indent=2, sort_keys=True)
        fh.write("\n")

    md = [
        f"# Sweep report — {name}",
        "",
        f"- {len(points)} LHS points × {len(seeds)} seeds × {len(variants)} variants = "
        f"{len(jobs)} runs in {elapsed:.0f}s ({report['seconds_per_run']}s/run)",
        f"- stable points (no LS §10 criterion tripped in any run): {sum(stable)}/{len(points)} "
        f"({stable_fraction:.0%})",
        f"- largest connected stable component: {component:.0%} of swept volume "
        f"(package pass needs ≥20%, Sim Plan §6) → **{'PASS' if report['package_pass'] else 'FAIL'}**",
        "",
        "## Run-level trip reasons",
        "",
    ]
    md += [f"- {k}: {v}" for k, v in sorted(trip_reasons.items())] or ["- none"]
    md += ["", "## Per-parameter trip rate (low / mid / high tercile)", ""]
    for name_, s in report["sensitivity"].items():
        md.append(f"- `{name_}`: {s['trip_rate_by_tercile_low_mid_high']}")
    (out_dir / f"{sweep_cfg['name']}_summary.md").write_text("\n".join(md) + "\n", encoding="utf-8")
    print(f"\nstable {sum(stable)}/{len(points)} ({stable_fraction:.0%}); "
          f"largest component {component:.0%}; report -> {out_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

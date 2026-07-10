"""Kill-criteria evaluation (Launch Spec §10) as automated checks over run outputs.

Launch Spec v0.3 §10 names this module the operative authority for the supply
criterion. The operative formulation is v3, adopted after positive-control
validation falsified v2 (DECISIONS #29–#31):

  v1  margin + convexity + bootstrap grace — ~5% per-run false positives
      (shock-recovery transients).
  v2  v1 + magnitude floor 0.5 — clean against honest noise, but the convexity
      streak is brittle against stochastic reality: scripted credit spirals with
      noisy epoch rates evaded it (positive controls A/B failed).
  v3  windowed excess growth. For window lengths W ∈ {6, 12} transitions
      (entirely post-grace), the statistic is

          E(W) = Σ Δlog(credit)
                 − max(0, Σ Δlog(volume_qualified))
                 − max(0, Σ Δlog(active_agents))

      over each sliding window; the criterion trips when E(W) meets its
      empirically derived noise floor F(W). Floors are set from the honest-noise
      study (sweep/derive_noise_floor.py; results/sweep_reports artifacts) at
      1.25 × the maximum honest E(W) over the full parameter space INCLUDING
      growing-economy runs. Multi-scale windows catch slow spirals a single short
      window would let compound indefinitely; W=3 is excluded (honest transients
      and 3-epoch spiral segments overlap, DECISIONS #32).

      The active-agents term (DECISIONS #34) fixes growth-induced false positives:
      a growing exchange onboards agents who draw credit lines before their
      settlement volume ramps, so credit-to-volume rises during onboarding and
      reads as a mild spiral. Subtracting agent-count growth removes exactly that
      confound — a real spiral inflates credit PER agent (count flat, term = 0,
      spiral still caught), while healthy growth inflates credit WITH the agent
      count (term cancels it). Validated by control E's growth scenarios.

  Denominator integrity: volume is the WASH-FILTERED series
  (settled_volume_qualified_ergs — wash-review-upheld and challenged-agent
  volume excluded, DECISIONS #30). Otherwise concurrent wash-inflated volume
  camouflages a credit spiral (the denominator attack; positive control C).
  Rows lacking the qualified column fall back to raw volume — simulation
  fixtures only; the production series is the qualified one.

Other criteria (unchanged): socialization and dispute rates trip epoch-level;
auditor recall is cumulative; any ledger-invariant violation is the sim-level
"settlement forgery / credit-line inflation" Adversary finding.

Production note: the floor VALUES are simulation-derived and do not transfer to
testnet — re-derive them from testnet honest-noise data during the bootstrap
grace window with the same script. The methodology transfers; the numbers don't.
"""

from __future__ import annotations

import math

# Windowed-excess floors F(W), DERIVED — sweep/derive_noise_floor.py, committed
# artifact results/sweep_reports/noise_floor_derivation.json. Set at SAFETY=1.25 ×
# max honest E(W) over the full parameter space (2,709 honest runs × all demand
# variants), at grace=12 (where the credit bootstrap has settled — honest E(6)
# stops falling), restricted to scales that separate honest noise from the
# should-trip controls with real margin:
#   W=6:  honest_max 0.368, floor 0.46, weakest control 0.605  → margin 0.15
#   W=12: honest_max 0.501, floor 0.63, weakest control 1.069  → margin 0.44
# W=3 is EXCLUDED: at 3-epoch scale honest transients (0.34) and genuine 3-epoch
# spiral segments (0.30) overlap — the scale cannot discriminate (DECISIONS #32).
SUPPLY_GRACE_EPOCHS = 12
SUPPLY_FLOORS = {6: 0.46, 12: 0.63}
SOCIALIZATION_MAX = 0.05
DISPUTE_MAX = 0.10
RECALL_MIN = 0.80


def _windowed_excess_at_grace(credit: list[float], volume: list[float],
                              agents: list[float] | None, grace_epochs: int,
                              window: int) -> list[tuple[int, float]]:
    """E over every complete post-grace window of one length: [(end_epoch, E)].
    Single source of truth for both the live criterion and the noise-floor
    derivation, so they can never drift apart (sweep/derive_noise_floor.py
    imports this exact function). `agents` is the active-agent count series;
    pass None to disable the growth-normalization term."""
    dlog_c: list[float | None] = []
    dlog_v: list[float | None] = []
    dlog_a: list[float] = []
    for i in range(1, len(credit)):
        epoch = i + 1
        if epoch <= grace_epochs or min(credit[i], credit[i - 1],
                                        volume[i], volume[i - 1]) <= 0:
            dlog_c.append(None)
            dlog_v.append(None)
            dlog_a.append(0.0)
        else:
            dlog_c.append(math.log(credit[i] / credit[i - 1]))
            dlog_v.append(math.log(volume[i] / volume[i - 1]))
            if agents is not None:
                a_cur, a_prev = max(1.0, agents[i]), max(1.0, agents[i - 1])
                dlog_a.append(math.log(a_cur / a_prev))
            else:
                dlog_a.append(0.0)
    series: list[tuple[int, float]] = []
    for start in range(0, len(dlog_c) - window + 1):
        seg_c = dlog_c[start:start + window]
        seg_v = dlog_v[start:start + window]
        seg_a = dlog_a[start:start + window]
        if any(x is None for x in seg_c):
            continue
        end_epoch = start + window + 1  # transition i covers epochs i+1 -> i+2
        e = sum(seg_c) - max(0.0, sum(seg_v)) - max(0.0, sum(seg_a))
        series.append((end_epoch, e))
    return series


def supply_excess_series(credit: list[float], volume: list[float],
                         agents: list[float] | None,
                         grace_epochs: int) -> dict[int, list[tuple[int, float]]]:
    """E(W) for every operative window length, keyed by W."""
    return {w: _windowed_excess_at_grace(credit, volume, agents, grace_epochs, w)
            for w in SUPPLY_FLOORS}


def evaluate(epoch_rows: list[dict], invariant_violations: list[str],
             grace_epochs: int | None = None) -> dict:
    """Evaluate all five §10 criteria over a run's epoch rows. The supply
    criterion's grace defaults to the derived SUPPLY_GRACE_EPOCHS; tests may
    override it explicitly."""
    grace = SUPPLY_GRACE_EPOCHS if grace_epochs is None else grace_epochs
    credit = [float(r["credit_outstanding_ergs"]) for r in epoch_rows]
    volume = [float(r.get("settled_volume_qualified_ergs", r["settled_volume_ergs"]))
              for r in epoch_rows]
    agents = ([float(r["n_active"]) for r in epoch_rows]
              if all("n_active" in r for r in epoch_rows) else None)
    socialization = [float(r["socialization_rate"]) for r in epoch_rows]
    disputes = [float(r["dispute_rate"]) for r in epoch_rows]
    seeded = sum(int(r["auditor_seeded"]) for r in epoch_rows)
    detected = sum(int(r["auditor_detected"]) for r in epoch_rows)

    # -- 1. supply stability (v3 windowed excess) -----------------------------
    excess = supply_excess_series(credit, volume, agents, grace)
    windows_detail = {}
    supply_tripped = False
    for window, floor in SUPPLY_FLOORS.items():
        series = excess[window]
        crossings = [(epoch, e) for epoch, e in series if e >= floor]
        max_e = max((e for _, e in series), default=None)
        windows_detail[window] = {
            "floor": floor,
            "max_E": round(max_e, 5) if max_e is not None else None,
            "first_trip_epoch": crossings[0][0] if crossings else None,
        }
        if crossings:
            supply_tripped = True

    soc_bad = [i + 1 for i, s in enumerate(socialization) if s > SOCIALIZATION_MAX]
    disp_bad = [i + 1 for i, d in enumerate(disputes) if d > DISPUTE_MAX]
    recall = detected / seeded if seeded else 1.0

    result = {
        "supply_superlinear": {
            "tripped": supply_tripped,
            "windows": windows_detail,
            "detail": "; ".join(
                f"W={w}: maxE={d['max_E']} floor={d['floor']}"
                + (f" TRIP@e{d['first_trip_epoch']}" if d["first_trip_epoch"] else "")
                for w, d in windows_detail.items()),
        },
        "socialization_gt_5pct": {
            "tripped": bool(soc_bad),
            "detail": f"epochs {soc_bad}" if soc_bad else
                      f"max {max(socialization):.4f}" if socialization else "no data",
        },
        "dispute_rate_gt_10pct": {
            "tripped": bool(disp_bad),
            "detail": f"epochs {disp_bad}" if disp_bad else
                      f"max {max(disputes):.4f}" if disputes else "no data",
        },
        "auditor_recall_lt_80pct": {
            "tripped": recall < RECALL_MIN,
            "detail": f"cumulative recall {recall:.4f} ({detected}/{seeded} seeded)",
        },
        "adversary_finding": {
            "tripped": bool(invariant_violations),
            "detail": (f"{len(invariant_violations)} invariant violation(s): "
                       f"{invariant_violations[:3]}") if invariant_violations else
                      "no ledger-invariant violations",
        },
    }
    result["any_tripped"] = any(v["tripped"] for k, v in result.items() if k != "any_tripped")
    return result

# Calibration — smoke-sweep findings and the road to the full sweep

Draft memo per Sim Plan §7.2, based on the executed smoke sweep (60 Latin-hypercube points
× 3 seeds × 3 demand variants = 540 runs). The full §4 sweep (300 points × 50 seeds × 3
variants) is built and ready; instructions and runtime below. Numbers here are indicative —
the smoke sweep exists to check the machinery and see the shape of the region, not to set
launch values.

## How to run

```powershell
# smoke (executed for this memo): ~3–4 minutes on 16 cores
.\.venv\Scripts\python.exe sweep\run_sweep.py sweep\smoke.yaml

# full Sim Plan §4 sweep: 45,000 runs, measured ~4.9 s CPU per run
# ⇒ ≈ 4.5–5 h wall-clock on this machine (14 workers). Run overnight:
.\.venv\Scripts\python.exe sweep\run_sweep.py sweep\full.yaml
```

Reports land in `results/sweep_reports/<name>_summary.{md,json}` — stable fraction, largest
connected stable component (the Sim Plan §6 package gate is ≥20% of swept volume), run-level
trip reasons, and per-parameter trip-rate terciles. Per-point detail (parameters, which
criterion tripped) is in the JSON.

## Smoke-sweep results

540 runs (60 points × 3 seeds × {baseline, −50% shock, +50% shock}), 457 s wall on 14
workers (~4.9 s CPU/run):

- **48/60 points stable (80%)** — no Launch Spec §10 criterion tripped in any seed or
  shock variant.
- **Largest connected stable component ≈ 63% of swept volume** → the Sim Plan §6
  package gate (contiguous region ≥ 20%, shock-robust) **passes at smoke scale**. This is
  indicative, not conclusive: 3 seeds per point and 60 points in a 10-dimensional cube.
- **Every trip is supply-superlinearity** (13 of 540 runs, concentrated in 12 points); no
  point tripped socialization, disputes, auditor recall, or invariant violations. The
  monetary core, not the institutions, is where the parameter risk lives.
- **Sensitivity (trip rate by tercile, low/mid/high — small-n, read as direction only):**
  - `settlement_fee_init` [0.25, 0.00, 0.35] — the sharpest dial: both very low (<0.5%)
    and very high (>1.7%) launch fees destabilize; the mid band around the 1% launch
    hypothesis is the calmest strip in the sweep.
  - `d_erg` [0.20, 0.10, 0.30] and `l_cap_mult` [0.15, 0.15, 0.30] — high collateral
    values and high credit caps *increase* trips: bigger floors and caps mean more
    drawable credit per agent, which is exactly the fuel of a supply spiral. The launch
    hypotheses (D_erg = 8, cap = 10×) sit in the calm middle.
  - `alpha` [0.25, 0.25, 0.10] — higher turnover credit is *safer* in this range:
    earned-credit headroom absorbs demand swings that floor-only credit turns into
    funding cliffs.
  - Remaining dimensions show no strong monotone signal at this sample size.

Recommended center for the full sweep: keep the Launch Spec §8 hypotheses (they sit
inside the stable component) and let the 50-seed sweep draw the region's edges,
especially the fee corridor and the D_erg × L_cap credit-fuel interaction.

## What the build itself established (independent of the sweep)

1. **The supply-stability criterion needed sharpening before it was usable.** Naively
   applied, LS §10's "credit outstanding growing superlinearly to volume for 3 epochs" trips
   on *every* honest launch: mutual-credit supply necessarily grows from an empty ledger
   toward its plateau, outpacing flat volume during ramp-up. First smoke pass: 60/60 points
   "failed", all solely on this criterion, none on any other. The checker now requires
   log-convexity (non-decreasing growth rates — the actual signature of a spiral) plus a
   grace window while the credit system's own trailing window fills (DECISIONS #13).
   **Adopted:** Launch Spec v0.3 §10 codifies exactly this formulation and names this
   repository's killcriteria.py as the operative authority — Path A's first finding to
   round-trip into the constitution (alignment audit in DECISIONS #28).
2. **Wash resistance holds, but through the full LS §9 stack, not any single rule.** The
   S1 leakage ordering (same-principal exclusion → same-lineage exclusion → detector +
   Auditor review + agent-level challenge-and-exclusion + counting caps) each removed its
   layer of the attack; the final full-evasion variant *retards* the activation clock
   (−7.8% per attempted wash settlement). Two detector lessons that generalize: statistical
   flags must use median/MAD (mass attacks shift the mean/sd of the distribution they are
   judged against), and wash under mutual credit has a balance-sheet identity — near-zero
   net flow at high gross against a concentrated counterparty set — because collateralized
   floors force rings to recirculate (DECISIONS #26).
3. **The collateralization invariant does its arithmetic job.** S4: extraction exactly zero
   at every D_erg in {3, 5, 8, 12}, farmed or not. Residual honestly noted: at low D_erg,
   turnover farming achieved credit lines above bond value before flags caught up —
   throughput, not rules, bounded the loss. Low-D_erg configurations lean on the wash
   detector; D_erg ≥ 8 does not.
4. **Reputation rents are real and bounded.** Adaptive pricers settle ~1.3–1.5× believed
   cost against honest 1.15× — the WP §4.4(c) pricing-power channel working, stabilized by
   competition; no runaway.
5. **Quality stratification is the honest baseline's dominant structure.** Winner-take-most
   matching concentrates work; the bottom half of the population drifts to its credit floor
   and freezes (suspension guard holding, LS §13.3). Credit outstanding plateaus at roughly
   (pinned agents × floor); the *level* of credit-to-volume (≈3–3.5 at baseline) is
   structural, not pathological — which is exactly why the kill criterion is about growth.
6. **Activation-clock integrity is bounded by Auditor review accuracy.** Post-review wash
   leakage scales with (1 − sensitivity); at the 0.90 stub value the challenge mechanism
   catches persistent rings anyway. The full sweep should treat auditor sensitivity as a
   sensitivity axis even though the Sim Plan fixes the seed rate.

## Full-sweep methodology notes

- The §6 package gate (contiguous stable region ≥20% of swept volume, robust to demand
  shocks) is evaluated exactly as in the smoke sweep, at 5× point density and 50 seeds.
- Attack scenarios: run the seven scenarios at representative stable points (center of the
  largest component + 3–5 spread points), not at all 300 — scenario × point × seed is
  compute-quadratic and the scenarios' defense verdicts vary with few parameters (D_erg,
  detector thresholds, β).
- After the full sweep: carry recommended values into the next Launch Spec
  parameter-registry revision with per-parameter sensitivity from the tercile trip rates,
  per Sim Plan §7.5 (deliverable 5 named it "v0.3"; that version number was consumed by
  the §10 kill-criterion revision, so the registry update targets the revision after).

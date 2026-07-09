# Calibration — full-sweep results and the §8 parameter-registry recommendation

Final memo per Sim Plan §7.2/§7.5, based on the executed **full sweep** (300 Latin-hypercube
points × 50 seeds × 3 demand variants = 45,000 runs, 3.8 h wall on 14 workers) and the smoke
sweep (60 × 3 × 3 = 540 runs). Attack-scenario evidence from `results/scenario_reports/`
feeds the per-parameter verdicts.

## How to run

```powershell
# smoke sweep: ~3 min on 16 cores
.\.venv\Scripts\python.exe sweep\run_sweep.py sweep\smoke.yaml

# full Sim Plan §4 sweep: 45,000 runs, ~3.8 h on this machine
.\.venv\Scripts\python.exe sweep\run_sweep.py sweep\full.yaml

# derive the v3 supply-criterion noise floors (auditable; regenerates the artifact)
.\.venv\Scripts\python.exe sweep\derive_noise_floor.py

# positive/negative controls and the detector-DoS mirror
.\.venv\Scripts\python.exe scenarios\controls_positive.py
.\.venv\Scripts\python.exe scenarios\control_e_detector_dos.py
```

Reports land in `results/sweep_reports/<name>_summary.{md,json}`, with per-run checkpoints in
`<name>_runs.jsonl` (survives a killed sweep; runs are seed-deterministic and individually
re-executable). Contiguity is the largest mutual-3-NN component of stable points — distance-
radius estimators are meaningless in a 10-dimensional cube, where pairwise distances concentrate.

## Headline result

**Package-level PASS (Sim Plan §6).** The economy is stable across the entire Sim Plan §4
parameter space: under the final (v3) kill criterion the full 45,000-run re-certification is
**300/300 points stable, 0 trips of any class, 100% contiguous region** (smoke 60/60). The §10
kill criteria do **not** bind anywhere in the swept ranges — the launch registry's hypotheses
survive unchallenged.

> **v3 re-certification sweep: COMPLETE.** 300 points × 50 seeds × 3 demand variants =
> 45,000 runs, 5.9 h. This is the out-of-sample gate — the floors are 1.25× the max over 3
> seeds/point; the sweep tested 50 seeds/point and found **zero** false trips, confirming the
> safety factor holds against seeds the derivation never saw. Result in `full_summary.json`.

What Path A actually found — four times over — is that the *criterion*, not the economy, was
the unstable object. Every §10 supply-criterion defect below was caught in simulation before it
could halt (or fail to halt) a production exchange. **This is the highest-value output of the
entire Path A effort.**

## The criterion story (the sweep's real deliverable)

The supply kill-criterion went through four formulations. Each fixed a defect the previous
one hid; the progression is the single most important thing Path A produced, because every
defect was in the constitution's *instrumentation*, caught in simulation before production.
**Negative controls alone (noise doesn't trip) validated v1 and v2 — and both were wrong.
Only positive controls (real spirals must trip) exposed the failures.**

1. **v0 (spec as written): halts every launch.** "Credit outstanding growing superlinearly
   to volume for 3 epochs" trips during any mutual-credit bootstrap — supply must outgrow
   flat volume while filling from an empty ledger. First smoke pass: 60/60 points "failed",
   all on this criterion. Fixed with log-convexity + a bootstrap grace window (DECISIONS #13);
   codified in Launch Spec v0.3 §10.
2. **v1 (convexity + grace): ~5% per-run false-positive rate.** The full sweep tripped
   2,299 of 45,000 runs — all supply-class, uniform across parameter space, 63% in shock-up
   variants. Deterministic re-execution measured the streaks: median cumulative Δlog(credit)
   0.14, p99 0.26, **max 0.38**, credit never above 22% of its structural ceiling; even the
   launch center tripped 6/150. Shock-recovery transients, not spirals. (DECISIONS #29.)
3. **v2 (v1 + magnitude floor 0.5): clean against noise, but BLIND to real spirals.** The
   magnitude floor cleared the transients (0 trips on re-evaluation). But **positive controls
   falsified it**: v1/v2's convexity *streak* resets on a single decelerating epoch, so a
   scripted ×1.35/epoch credit-line-inflation spiral (control A) evaded it in 2 of 3 seeds,
   and a detector-blind Sybil farm (control B) evaded in all 3. A criterion that noise doesn't
   trip *and spirals don't trip either* is not conservative — it is broken. (DECISIONS #29.)
4. **v3 (windowed excess growth): validated in both directions.** The streak is replaced by a
   scale-windowed statistic that does not depend on epoch-to-epoch smoothness. For W ∈ {6, 12}
   post-grace transitions,

   > E(W) = Σ Δlog(credit) − max(0, Σ Δlog(volume_qualified)) − max(0, Σ Δlog(active_agents))

   trips when any E(W) ≥ its derived floor F(W). Three design decisions, each forced by data:
   - **Wash-filtered denominator** (DECISIONS #30): volume is the qualified series (wash-upheld
     and challenged-agent volume removed). Defeats the volume-padding camouflage — control C
     (spiral + padded volume, detector on) trips because the detector strips the padding
     (raw/qualified volume diverge 13.4k → 6.8k ergs), where a raw-volume denominator would be
     fooled.
   - **Active-agent normalization** (DECISIONS #34): subtracting agent-count growth removes the
     growth-induced false positive a static-population noise model missed entirely (see Control
     E below).
   - **W=3 excluded** (DECISIONS #32): at 3-epoch scale honest transients (0.34) and genuine
     3-epoch spiral segments (0.30) overlap — the scale cannot discriminate, so it is dropped
     rather than fudged.

**Carry into the next Launch Spec §10 revision:** the v3 formulation — grace 12, windows
{6, 12}, floors {0.46, 0.63}, wash-filtered + agent-normalized statistic — with the standing
caveat that the floor *values* are re-derived on testnet data (below).

### Full-sweep reclassification, made explicit

The same 45,000 honest runs, classified under each criterion version. The 2,299 v1 trips were
not quietly dropped — they were deterministically re-executed, their streak magnitudes measured
(committed in `results/sweep_reports/v1_trip_magnitudes.json`, 510 KB, every trip auditable),
and shown to be shock-recovery transients (max 0.38 log-points vs a spiral's 0.55+). The
reclassification *is* the finding:

| Criterion | Run-level trips / 45,000 | Stable points / 300 | Why the count changed |
|---|---|---|---|
| v1 (convexity + grace) | 2,299 | 1 | baseline: honest transients counted as spirals |
| v2 (+ magnitude floor 0.5) | 0 | 300 | transients (max 0.38) fall below the 0.5 floor; **but v2 also missed real spirals** — falsified by positive controls |
| v3 (windowed excess, normalized) | **0** | **300** | scale-windowed statistic is not streak-brittle; agent-normalized denominator prevents growth false positives — **and positive controls confirm it still catches real spirals** |

v2 and v3 agree that the honest economy is stable (0 trips); they differ on whether *spirals*
are caught, which the sweep cannot show (it contains no spirals) and only the positive controls
can. That is precisely why the controls, not the sweep, are the load-bearing validation of v3.

## How the floors were derived (so a reviewer can audit, not trust)

Floors are **not asserted**; they are the committed output of `sweep/derive_noise_floor.py`
(artifact: `results/sweep_reports/noise_floor_derivation.json`). Method:

1. Run the honest economy across the **full parameter space** — all 300 LHS points × 3 seeds ×
   3 demand variants (2,709 runs) — plus **growing-economy honest runs** (5–25 agents/epoch)
   so the noise model matches a launching exchange, plus the four controls.
2. For each run measure the peak E(W) at every (grace ∈ {7,10,12,14}, window ∈ {3,6,12}).
3. Set F(W) = **1.25 × max honest E(W)** (the safety factor: a 25% band above the worst honest
   run anywhere in the swept space, so an unlucky honest seed does not trip).
4. Keep only (grace, window) scales where F(W) sits **below** the weakest should-trip control
   with real margin. Report the margin; drop scales that overlap.

**Separation table (grace 12, the operative floors):**

| Window | honest p50 | honest p99 | honest max | floor (1.25×) | weakest spiral (A/C/D) | negative ctl B | margin |
|---|---|---|---|---|---|---|---|
| W=6  | 0.171 | 0.315 | 0.368 | **0.46** | 0.524 (D) | 0.171 | **+0.064** |
| W=12 | 0.245 | 0.428 | 0.501 | **0.63** | 0.981 (D) | 0.299 | **+0.354** |

W=6 detects fast (latency ~8 epochs) but its margin is thin (0.064) against the gentlest
spiral (control D, ×1.18/epoch); W=12 is the wide-margin backstop for slower spirals. Below
~×1.055/epoch a spiral sits inside honest noise and is indistinguishable — the honest floor of
detectability, stated plainly. The negative control (ring-farming) never exceeds 0.30 at any
scale, well clear of both floors.

## Positive & negative controls (validation in both directions)

`scenarios/controls_positive.py`, run on in-sample (42–44) and out-of-sample (100–102) seeds.
Each control declares whether it *should* trip; certification requires every should-trip
control to trip and every should-not control to stay silent.

| Control | Design | Should trip | Result | Latency W6 / W12 |
|---|---|---|---|---|
| **A** credit-line inflation | lines ×1.35/epoch, detector on | yes | ✅ trips (+ adversary_finding) | ~8 / 14 |
| **B** ring-farming | Sybil rings, wash detector DISABLED | **no** | ✅ silent (all seeds) | — |
| **C** camouflaged spiral | A + wash-padded volume, detector on | yes | ✅ trips (padding stripped) | 8 / 14 |
| **D** clean distributed spiral | ×1.18/epoch under L_cap, detector on | yes | ✅ trips (**supply criterion alone**) | ~8 / 14 |

Control B is *correctly* silent: balanced rings net to zero in credit outstanding (the Sybil
cohort's aggregate negative balance is pinned all run), so ring-farming inflates volume, not
credit stock — a fake-volume attack (the detector's domain, disabled here by construction), not
a spiral. Under valid mutual-credit accounting a credit spiral is only reachable by inflating
recorded lines outside settlement, which controls A/C/D exercise and which leaves two
complementary signatures: the supply criterion (E(W)) and, past L_cap, a ledger-invariant
violation. Control D isolates the supply criterion by staying under L_cap — it trips with **no**
invariant backstop, proving the supply criterion itself carries the detection. (DECISIONS #31.)

## Control E — the detector-DoS mirror, and the growth finding it surfaced

The wash-filtered denominator (#30) raises a mirror risk: an adversary who induces wash
FALSE-POSITIVES against honest counterparties shrinks the qualified denominator, potentially
inflating honest E(W) toward the floor (a denial-of-service on the honest exchange).
`scenarios/control_e_detector_dos.py` measured it. Two results:

1. **The detector-DoS is a non-threat.** A *constant* induced-FP fraction cancels in the
   log-difference (Δlog of a constant-scaled series is unchanged), so it moves E(W) by 0. A
   *ramped* suppression adds < 0.01, because net qualified volume still grows faster than the
   ramp strips it. No EMA-damped denominator is required; damping would not even have helped.
2. **It surfaced a bigger bug the static-population sweep hid: growth-induced false positives.**
   A legitimately *growing* exchange (continuous registration, LS §4) false-tripped at **zero
   attack** — honest E(12) hit 0.66 (> the 0.63 floor) at 25 agents/epoch onboarding, because
   new agents draw credit lines before their settlement volume ramps, so credit-to-volume
   rises during onboarding and reads as a mild spiral. **Fix:** the active-agent term
   (DECISIONS #34). A real spiral inflates credit *per agent* (count flat → term 0 → still
   caught: controls A/D unchanged at E(12) ≈ 1.0); healthy growth inflates credit *with* the
   agent count (term cancels it: growth-25 honest E(12) 0.66 → 0.30). After the fix, Control E
   clears every floor under ramped suppression on a growing economy at every induced-FP rate
   tested (0–40%):

   | scenario | E(6) | E(12) | floors 0.46 / 0.63 |
   |---|---|---|---|
   | ramp + growth 10/epoch | 0.21 | 0.34 | clears |
   | ramp + growth 25/epoch | 0.20 | 0.30 | clears |

   This is a concrete instance of why production floors cannot be inherited from simulation:
   the static-population noise model missed an entire class of honest behavior until a positive
   control forced it into view.

## Coupled-subsystem CI lock

Because the criterion's denominator now depends on the wash detector, the floors depend on two
subsystems: detector parameters and killcriteria code. `src/agora/calibration_lock.py` hashes
(killcriteria source + detector config block); the derivation stamps that hash into its
artifact; `tests/test_calibration_lock.py` **fails** if either changes without a matching
re-derivation. Coupled subsystems re-calibrate together or the build breaks — they cannot
silently drift. (DECISIONS #33.)

## Production floors do not transfer from simulation — re-derive them on testnet

**The floor VALUES here (grace 12, F(6)=0.46, F(12)=0.63) are simulation artifacts and must
not be shipped to production.** They were derived from this simulation's honest-noise
distribution, which reflects this model's agent mix, demand process, capacity dynamics, and
onboarding rate — none of which will match a live testnet exactly. Control E already
demonstrated the failure mode: a noise model missing continuous-registration growth produced
floors that false-tripped a growing economy, until growth was added to the sample. A different
production reality (different growth curve, different default rate, different task-size
distribution) will shift the honest E(W) distribution again.

**The methodology transfers; the numbers don't.** During the bootstrap grace window on testnet
— while credits are still valueless and no halt has consequences — run
`sweep/derive_noise_floor.py` against the *testnet's own* honest-epoch data (pass the testnet
seeds), inspect the separation table against the same positive controls, and set the production
floors from that. Then let the CI lock (above) hold the detector/criterion/floor triple
together for the rest of the deployment. The simulation's contribution is the *shape* of the
criterion (windowed excess, wash-filtered and agent-normalized denominator, the scales that
separate, the 1.25× safety factor, the positive/negative control battery) — not the specific
thresholds.

## §8 parameter-registry recommendation (Sim Plan deliverable 5)

Stability does not discriminate within the swept ranges, so recommendations rest on the
scenario evidence and mechanism findings. **Verdict: retain every §8 launch hypothesis.**

| Symbol | Launch value | Recommendation | Evidence |
|---|---|---|---|
| D_erg | 8 ergs | **Keep 8; treat ≥ 6.7 as a hard floor, ≥ 8 as the safe margin** | Supply-stability indifferent (flat terciles). S4: at every tested D_erg extraction = 0, but below 200/30 ≈ 6.7 the credit floor contracts and turnover farming achieved lines *above* bond — Sybil defense then leans on the wash detector rather than arithmetic. D_erg ≥ 8 keeps the collateralization invariant self-enforcing. |
| α | 0.25 | Keep 0.25 | Stable across 0.05–0.6; v1 noise mildly favored higher α (earned headroom smooths demand swings). 0.25–0.5 all defensible. |
| β | 0.005 | Keep 0.005 | Stable across 0.001–0.03. S6: fee-bleed attack uneconomic at 0.005 (capacity decay escapes it). Note: β prices *listed capacity*, and at no swept value does it counteract quality concentration — that is matching-driven, not a β dial. |
| settlement fee | 1.0% | Keep 1.0% | Converges to the ~0.7–0.9% cost-recovery band within 2–3 epochs from the 1.0% start; both sweep extremes (<0.5%, >1.7%) showed elevated v1 noise. |
| L_cap | 10 × L_floor | Keep 10× (scaling L_floor_active, DECISIONS #12) | Stable across 3–25×. |
| p* | 0.50 | Keep 0.50 | Stable across 0.35–0.65; basket calibration hits the target by construction and the epoch-6 retarget stays inside δ under attack (S2). |
| k | 25 | Keep 25 | No stability or scenario signal across 5–100. |
| λ | 2.0 | Keep 2.0 — **flag as untested-in-anger** | No version transitions occur in Path A scope; λ never binds. Path B should not treat it as calibrated. |
| Kleos half-life | 180 d | Keep 180 d | Stable across 60–540 d; S7's patient-cluster share *decays* under it. |
| capacity_min | 1 task/epoch | Keep 1 | Stable across 1–5. |
| Jury size / seed rate / duty quota | 5 / 2% / 8 | Keep | Not stressed beyond stubs (disputes stochastic per Sim Plan §1; seed rate fixed per §4). |

**Registry additions Path A recommends the spec adopt as named parameters:** the v3
supply-criterion constants (grace 12, windows {6, 12}, floors {0.46, 0.63}, safety factor
1.25 — the floors flagged as re-derive-on-testnet per the section above); the wash-detector
thresholds (bidirectionality requirement, conservation net-ratio 0.12 with top-3-counterparty
share 0.70, trivial-spam share/count floors 0.5/8, robust-z 3.0 on median/MAD); the agent
challenge threshold (10 review-upheld flags, LS §9 exclusion-pending-resolution); and Auditor
review sensitivity (0.90 stub) — activation-clock integrity degrades roughly linearly in
(1 − sensitivity), so it belongs in the registry, not in the implementation's shadows. The
criterion now formally depends on the detector parameters (they define the qualified
denominator), so the spec should note the two are a **coupled calibration unit** (DECISIONS
#30, #33).

## Attack-scenario verdicts at the recommended registry (unchanged from M5)

S1 wash rush: negative leakage in all three disclosure variants (full evasion −7.8%/attempt).
S2 median drag: SCU drift 0.006 difficulty units, inside δ. S3 capacity flood: envelope binds,
94% overflow, victim income 0.97× twin. S4 Sybils: extraction 0 at every D_erg (caveat above).
S5 griefing: strictly positive attacker cost. S6 fee bleed: both policies escape via capacity
decay. S7 patience: peak decisive power 28.8%, below the ⅓ blocking threshold, decaying.

## Residual risks and honest caveats

- **Auditor accuracy is the soft underbelly**: wash-flag review at 0.90 sensitivity leaves
  ~10% of true-wash flags cleared; the challenge mechanism catches persistent rings anyway,
  but the leakage floor scales with review error. Not a parameter dial — an operations bar.
- **Quality stratification** is the honest economy's dominant structure: winner-take-most
  matching pins the bottom half at its credit floor (suspension guard holding). The
  credit-to-volume *level* (~3–3.5×) is structural; only its growth is pathological.
- **λ and jury machinery** ship uncalibrated by design (out of Path A scope).
- Kill criteria that never bind in-sweep cannot *rank* parameter values; the registry
  verdicts above are "no evidence against the hypotheses + scenario support", not optima.
- **The supply criterion detects spirals ≥ ~×1.055/epoch sustained.** Slower credit spirals
  sit inside honest noise and are indistinguishable by this statistic — the honest floor of
  detectability, not a tunable. W=6 detects fast spirals within ~8 epochs; W=12 catches slower
  ones later. A patient sub-threshold spiral is a residual the constitution should know about.
- **The v3 floors are a coupled calibration unit with the wash detector and must be re-derived
  on testnet** (see the production-floors section). The CI lock enforces this in-repo; it
  cannot enforce it across the sim→testnet boundary — that is a deployment discipline.

## Go/no-go

**Go.** Path A's mandate — determine whether a stable operating region exists before any
contract is written (Sim Plan §6) — is answered affirmatively: the stable region is the entire
§4 sweep volume, the seven scripted attacks fail against the calibrated defenses, and the
supply kill-criterion is now validated in **both** directions (honest noise does not trip it;
positive controls confirm real spirals do). The four defects Path A found were all in the
constitution's own instrumentation — the §10 supply criterion — not in the economy:

1. v0 halted every launch at bootstrap → fixed (grace + log-convexity), **codified in Launch
   Spec v0.3 §10**.
2. v1 carried a ~5% false-positive rate on shock transients → fixed (magnitude floor).
3. v2 was blind to real spirals (streak brittleness) → fixed (windowed excess), **caught only
   because positive controls were demanded** — negative controls had passed it.
4. v3's wash-filtered denominator + a static-population noise model false-tripped growing
   economies → fixed (agent normalization + growth in the noise sample).

The through-line for Path B and the Launch Spec: **a kill criterion is itself a mechanism that
must be adversarially tested.** The composite supply criterion, its positive/negative control
battery, the auditable floor-derivation script, and the coupled-subsystem CI lock are as much a
Path A deliverable as the economic parameter region. Nothing in the economy resisted
validation; the instrumentation took four iterations — and would have shipped broken twice
(v1 over-halting, v2 under-halting) without the positive controls and the growth stress test.

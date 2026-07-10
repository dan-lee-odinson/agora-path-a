# Decisions

Interpretations made where the specs are ambiguous or silent. Rule from the build directive:
make the conservative choice, cite the section it interprets, continue. Entries are numbered
for citation from code docstrings ("DECISIONS #n").

---

**#1 — Integer milli-ergs.** All balances and transfers are integers denominated in milli-ergs
(1 erg = 1,000 mErg). *Why:* the core invariant — matched debit/credit pairs net to zero
system-wide (Whitepaper §4.1) — becomes exact integer arithmetic instead of float tolerance.
Fees round down (floor); the sub-milli-erg residue stays with the payer, never duplicated.
*Interprets:* WP §4.1–4.2, LS §13.1.

**#2 — V_90d on a 14-day epoch grid = trailing 6 epochs.** 6 × 14 = 84 days is the largest
whole-epoch window ≤ 90 days; the tighter window grants *less* uncollateralized credit, the
conservative direction. *Interprets:* LS §7 "0.25 × V_90d"; WP §4.5.

**#3 — V counts worker-side (earned) settled volume only, excluding wash-flagged settlements.**
WP §4.5 sizes credit to "demonstrated flow" on the real-bills principle — credit as working
capital against throughput of *performed* work. Counting buy-side volume would let an agent
inflate its own credit line by spending credit, a self-referential loop; counting wash-flagged
trades would let scenario-1-style rings farm credit lines. Both exclusions are conservative
(smaller lines). *Interprets:* WP §4.5, LS §7.

**#4 — Settlement fee is deducted from worker proceeds.** LS §13.1 fixes the buyer's debit at
exactly the escrowed quote, so the fee cannot be added on the buyer side; the worker receives
`quote − fee` and FeePool receives `fee`. WP §13.1's "from the transacting parties" is realized
through market pricing (workers price the fee into rates), not through double charging.
*Interprets:* LS §13.1 vs WP §13.1.

**#5 — Listing-fee units: capacity is declared in tasks.** LS §7 defines capacity_i as an
erg-volume but prices the fee as β × r_i × capacity_i, which is dimensionally erg² if capacity
is ergs. Resolution: agents declare capacity as a task count n_i; the acceptance-obligation
envelope is the erg-volume r_i × n_i; the fee is β × r_i × n_i per epoch (ergs, as intended).
This preserves both the §7 fee formula and the §7 "capacity_min = 1 median task/epoch" floor
with consistent units, and keeps capacity inflation self-taxing. *Interprets:* LS §7.

**#6 — "Same lineage cluster" = same lineage family tag.** LS §9 leaves "lineage cluster"
operationally undefined at sim level (fingerprint clustering is an emerging-tier capability,
WP §3). Using the coarser family tag disqualifies *more* settlements from activation counting —
conservative for the wash-resistance questions this sim exists to answer. Matches the build
directive's invariant test ("exclude same-principal and same-lineage trades"). *Interprets:* LS §9.

**#7 — Principal/pair caps applied as counting caps at aggregation.** The 15% principal and 2%
pair caps (LS §9) are enforced by capping each principal's (pair's) contribution to the
qualified-settlement total at the stated share of the capped total, solved iteratively at each
epoch close. A settlement beyond a cap remains a valid trade; it just does not advance the
activation clock — exactly the LS §9 wording. *Interprets:* LS §9.

**#8 — Failed verification refunds the poster in full; no fee; capacity already consumed stays
consumed for the epoch.** LS §13.4 lists settlement, withdrawal, invalidation, funding failure
as capacity release events; a failed verification is the settlement-path terminal event (escrow
resolves back to poster), the worker's slot was genuinely occupied, and the worker takes the
delivery-record hit (WP §7.1 Prong 3). No fee is charged because no settlement value transferred.
*Interprets:* LS §13.4, §2 verification procedure.

**#9 — Fee retarget with zero settled volume carries the prior rate forward.** The retarget
formula divides by settled_volume(t); an empty epoch would be undefined. Carrying the prior rate
is the least-surprise, least-action choice and matches "published, not smoothed" (LS §7) — no
synthetic value is invented. *Interprets:* LS §7, §13.2.

**#10 — Audited cost function.** Sim Plan §2 models audited cost as a function of settlement and
probe volume: `cost(t) = c_fixed + c_settle·settlements(t) + c_probe·probes(t) + socialized_losses(t)`,
with probes(t) = duty_quota × active_agents(t) (LS §8 duty quota, WP §6 civic compute). Socialized
losses enter cost per WP §4.5 ("audited loss line item within the balanced-budget fee").
Coefficients are calibrated so the equilibrium fee at baseline volume lands near the 1.0% launch
rate (LS §7), keeping the launch hypothesis internally consistent. *Interprets:* Sim Plan §2, WP §4.5/§13.1.

**#11 — System accounts for exact zero-sum.** ESCROW (funded quotes in flight), FEEPOOL (fee
intake), COST_SINK (extinguished expenditure), LOSS (written-off defaults). "Extinguishing
against verified operating cost" (WP §13.1) is modeled as FEEPOOL→COST_SINK transfers; default
write-offs are LOSS-account debits. Every erg movement in the sim is a matched transfer, so
`sum(all accounts) == 0` holds exactly at every step — the sim-level analogue of "no mint
function exists" (LS §6). *Interprets:* WP §4.2, §13.1; LS §6.

**#12 — L_cap scales the active floor.** LS §7/§8 state L_cap = 10 × L_floor with L_floor = 200;
when simulation lowers D_erg below ~6.67 the collateralization invariant contracts the floor
(L_floor_active = min(200, 30·D_erg)). L_cap is implemented as cap_mult × L_floor_active so the
whole credit schedule contracts with collateral — conservative; a fixed 2,000-erg cap over a
contracted floor would widen the uncollateralized band. *Interprets:* LS §7, §8.

**#13 — Superlinear-growth kill test.** LS §10 "credit outstanding growing superlinearly to
volume for 3 epochs" is operationalized as: 3 consecutive epochs in which
`Δlog(credit_outstanding) > max(0, Δlog(settled_volume)) + 0.02`. Credit growing 2 log-points
faster than volume (or growing while volume stalls) for 3 straight epochs trips the criterion.
The margin filters float-level noise; the `max(0,·)` term makes credit growth during volume
collapse count as superlinear, the conservative reading. Two qualifiers keep the criterion
aimed at the pathology §10 names rather than at every cold start: (a) evaluation begins after
the credit system's own trailing window has filled (epoch > v_window_epochs + 1); (b) the
streak requires *non-decreasing* Δlog(credit) — "superlinear" is log-convexity: an
equilibrating stock approaches its plateau at decaying rates (the mutual-credit bootstrap,
WP §4.2), while a spiral grows at non-decreasing rates. Path A feedback for the Launch Spec:
§10's supply criterion needs this precision in contract form, or every honest launch halts
itself during ramp-up. *Interprets:* LS §10.

**#14 — Disputes are stochastic outcomes.** Per Sim Plan §1 (out of scope: jury deliberation
content), each settlement candidate disputes with a small probability and overturns with a fixed
conditional probability; both are baseline-calibrated parameters, and dispute rate feeds the
LS §10 kill criterion. Jury mechanics are not simulated. *Interprets:* Sim Plan §1, LS §10.

**#15 — Epochs are numbered 1..26; the scheduled basket retarget executes at the close of
epoch 6.** LS §5.4 "one scheduled retarget at epoch 6". *Interprets:* LS §5.4.

**#16 — Kill criterion "Adversary finding of settlement forgery / credit-line inflation" maps to
runtime invariant violations.** The sim has no Adversary organ (Sim Plan scopes it to an auditor
stub); the equivalent evidence is any violation of the ledger invariants (zero-sum, credit-line
ceiling, collateralization) during a run — these are checked every epoch and any violation fails
the run's kill-criteria evaluation. Auditor seeded-fault recall is modeled with the Sim Plan §4
fixed 2% seed rate and a detection-sensitivity parameter. *Interprets:* LS §10, Sim Plan §4.

**#19 — Per-epoch envelope vs. reservation release.** LS §13.4 releases reserved capacity on
settlement, withdrawal, invalidation, and funding failure; LS §7 defines capacity as the
erg-volume the worker is "obligated to accept **per epoch**". These compose as: the epoch
acceptance envelope is consumed at funding; withdrawal and invalidation *restore* it (the work
never happened — the slot can be resold within the epoch); settlement and failed verification
leave it consumed (the slot was genuinely occupied — otherwise a worker could exceed its declared
per-epoch obligation by settling fast); funding failure never consumed anything. In this
discrete-epoch model every escrow resolves within its funding epoch, so no cross-epoch
reservation state exists. *Interprets:* LS §7, §13.4.

**#20 — SCU proxy and chain-linking.** The launch runs one category, so the sim's SCU measure
is the mean difficulty of the active basket. Difficulty is a location parameter on the logit
scale (it legitimately sits near or below zero), so the chain-link index is *additive*:
index += (after − before) at each retarget, starting at 0. Drift converts to the pass-rate
scale via the logistic slope (Δpass ≈ 0.25 · κ · Δdifficulty at center) for comparison with
the δ band. Richer SCU machinery has nothing to link at Tier 1. *Interprets:* WP §4.3, LS §5.4;
Sim Plan §5.2 "measure SCU drift".

**#25 — Retarget damping is reserve-bounded, worst-first.** LS §5.4 admits "pre-committed
reserve templates"; WP §16 (step 3) names "retarget damping caps per-epoch basket movement" as
a defense. Composition: retirements per retarget are capped at reserve availability so the
600-template basket never shrinks (the measuring rod keeps its length); when more templates
saturate than reserves exist, the highest pass rates retire first and the rest await the next
retarget. *Interprets:* LS §5.4; WP §4.3, §16.

**#26 — Conservation-ring detection is the settlement-graph correlation report.** LS §9's
clustering reports include "settlement-graph correlation". The sim implements the mutual-credit
form: an agent with high gross flow whose inflow ≈ outflow (|net|/gross ≤ 12%) is
conservation-flagged *when its trade is also concentrated* (top-3 counterparties ≥ 70% of its
settlements); settlements between two conservation-flagged agents are wash-flagged. Rationale:
a wash ring on collateralized floors *must* recycle what it receives every epoch — near-zero
net at high gross is wash's balance-sheet identity under mutual credit — but a fully-circulating
honest economy also nets near zero *against the whole market*, so the distinguisher is balance
against a tiny counterparty set. Catches long rings that evade pairwise-cycle and per-agent
threshold checks. *Interprets:* LS §9; WP §4.1.

**#21 — Counterparty-pair caps at principal granularity.** LS §9's "no single counterparty
*pair* for >2%" is read as a pair of disclosed operator principals (the sentence's subject is
operator-principal concentration). Principal-pairs aggregate more settlements than agent-pairs,
so the cap binds sooner — conservative: the activation clock only slows, and agent-level
pair-spam across one principal's fleet cannot evade it. Cap arithmetic is applied at
aggregation as counting caps with excess-per-breach deduction (see #7); overlapping breaches
deduct once per breach, which can only under-count qualified settlements. *Interprets:* LS §9.

**#22 — Demand assignment is budget-weighted; baseline circulation closes.** Sim Plan §3's
demand model gives posting principals "heterogeneous budgets"; the sim realizes a budget as the
poster's funding headroom (balance + credit line), assigning each exogenous task to a posting
agent with probability proportional to headroom. In the baseline all principals post
(posting_principal_frac = 1.0): a closed mutual-credit economy in which earnings recycle into
demand — the steady state the supply-stability question is *about*. Concentrated-consumption
structures (posting_frac < 1) are stress cases for scenarios and the sweep, not the calibration
baseline. *Interprets:* Sim Plan §3.

**#23 — Quality-adjusted matching.** Posters select the lowest *quality-adjusted* rate
(rate ÷ public rating, rating floored at 0.05) rather than the raw cheapest listing. Rationale:
a failed verification refunds the poster but wastes its epoch, so rational posters discount
rates by expected pass; and WP §4.4 channel (c) says the quality multiplier operates through
"the pricing power the agent can command through reputation" — with raw-cheapest matching that
channel cannot exist and the Harberger question ("delivered-quality-consistent pricing",
Sim Plan §1.2) is unanswerable by construction. Rating is the WP §7.2 Bayesian combination of
exam prior and delivery record. *Interprets:* WP §4.4, §7.2; Sim Plan §1.2.

**#24 — Wash flags resolve through stochastic Auditor review.** LS §9 makes flagged
settlements unqualified *pending Auditor review*; the Sim Plan scopes the Auditor to a stub.
The review is therefore modeled with the stub's sensitivity parameter (0.90 initial): an
honest flag is cleared with p = sensitivity, an adversarial flag survives with p =
sensitivity (ground truth known to the sim, exactly as with seeded faults). The epoch logs
publish raw flags (detector calibration) and the post-review residual (the system-level
cost honest agents actually bear). Settlements whose flags survive review stay unqualified
and are removed from credit-line turnover. *Interprets:* LS §9; Sim Plan §2, §4.

**#27 — Challenge-and-exclusion at the agent level.** LS §9 enforces the principal floor "by
challenge-plus-exclusion": *agents* under unresolved challenge are excluded from activation
counts. Sim realization: review-upheld wash flags accrue per-agent strikes; at 10 strikes the
agent is challenged and every settlement it touches stops advancing the clock permanently
(the sim has no resolution process to model). Ten review-upheld strikes at a 90%-accurate
review implies ~100 raw flags for an honest agent — orders of magnitude above the honest
baseline residual — so honest agents effectively never trip it, while ring members trip it
within an epoch or two. *Interprets:* LS §9; Sim Plan §5.1.

**#28 — Launch Spec v0.3 / Whitepaper v0.4 adoption audit.** LS v0.3 §10 rewrites the supply
kill-criterion to codify the Path A finding and names this repository's killcriteria.py "the
operative formulation, which is authoritative." Alignment audit of the spec's prose against the
code: (a) the spec summarizes the test as "credit-to-volume *ratio* exhibiting log-convex
growth"; the code's actual test is two-part and stated on the credit *stock* — every transition
in the streak must satisfy Δlog(credit) > max(0, Δlog(volume)) + 0.02, and Δlog(credit) must be
non-decreasing across the 3-transition streak. The formulations differ at the edges, in the
code's favor: a volume collapse with flat credit grows the ratio convexly but is a demand crash,
not a credit spiral (the code requires credit itself to grow ≥ 2 log-points per epoch); and
noisy volume can break ratio-convexity while stock-convexity correctly persists. (b) The spec's
"simulation-derived" bootstrap grace is v_window_epochs + 1 (= 7 epochs at launch values). No
conflict exists — the spec expressly defers to this code — but the next spec revision should
adopt the stock-based wording verbatim. Companion notes: Whitepaper v0.4's new sections (§1.1,
§1.2, §10.8, §10.9, §13.6) are governance/legal doctrine with no Tier-1 mechanism impact on
this simulation; Conflict Register item 8 is closed (WP §4.4 now states directly what LS §13.1
specified and this sim already implements, DECISIONS #4); WP v0.4's header names its companion
spec as "v0.2.3" while the operative launch spec is v0.3 — a doc-metadata nit for the next
whitepaper patch, noted here rather than edited into a frozen document. *Interprets:* LS v0.3
§10, Appendix A; WP v0.4.

**#29 — Supply-criterion magnitude floor (criterion v2), set by the full sweep.** The
45,000-run full sweep exposed a second defect in the supply kill-criterion: margin +
convexity alone has a ~5% per-run false-positive rate (2,299 trips, all supply-class, spread
uniformly across parameter space — no tercile of any swept dimension moves the rate — and
concentrated 63% in shock-up variants). Deterministic re-execution of every tripped run
measured the streaks: median cumulative Δlog(credit) 0.14, p99 0.26, maximum 0.38, with
credit never exceeding 22% of its structural ceiling (n_agents × L_cap) — shock-recovery
transients, not spirals. Even the launch-center configuration tripped 6/150 runs. v2 adds a
materiality floor: the accelerating streak must also accumulate ≥ 0.5 log-points (+65%) of
credit growth. 0.5 sits ~30% above the worst transient ever observed and far below any real
spiral (20%/epoch compounding = 0.55 in three epochs; doubling = 2.08). Production
translation: without the floor, an honest exchange accumulates ~5%/year probability of
spuriously halting itself. The floor only tightens the criterion, so untripped runs are
unaffected (monotonicity) — the full sweep re-evaluation under v2 re-runs only the 2,299
v1-tripped runs. Carry into the next Launch Spec §10 revision alongside #28's wording fix.
*Interprets:* LS v0.3 §10; Sim Plan §6.

**#30 — Supply-criterion denominator is wash-filtered qualified volume.** The v3 supply
statistic E(W) = Σ Δlog(credit) − max(0, Σ Δlog(volume)) subtracts volume growth, so a credit
spiral run concurrently with wash-inflated volume would camouflage itself by inflating the
denominator (the "denominator attack", positive control C). Resolution: the criterion's volume
series is `settled_volume_qualified_ergs` — settled volume minus settlements that are
wash-review-upheld or involve challenged agents (the same integrity filter the activation clock
uses, LS §9). Fees are still charged on ALL settlements (wash trades pay full freight — attacker
cost), but they do not count toward the criterion's denominator. Composition proof: control C
(spiral + padding, detector ON) trips because the detector strips the padding from the qualified
series; the same attack with the detector off (control B) is a different, detector-domain
problem (#31). *Interprets:* LS §10, §9; Sim Plan §6.

**#31 — Why ring-farming is not a supply spiral (control B reclassification).** Positive-control
B (S4 ring-farming, wash detector disabled) does not trip the supply criterion, and diagnostic
shows why this is correct rather than a miss: under valid mutual-credit accounting every erg of
credit outstanding is a settled erg (funding an escrow that settles), so the credit STOCK cannot
outgrow cumulative settled VOLUME — the c/v ratio is bounded. Balanced rings (A→B→C→A) net to
zero in credit-outstanding (the diagnostic pins the Sybil cohort's aggregate negative balance
constant for the entire run while their settlement count climbs), so ring-farming inflates
volume, never credit stock, and there is no spiral to detect. A genuine credit spiral (ratio
growing) is only reachable by inflating recorded lines/balances OUTSIDE settlement accounting —
the §10 "credit-line inflation" adversary class — which leaves two complementary signatures: the
growth-rate decoupling (supply criterion, controls A/C/D) and, once draws pass L_cap, a
ledger-invariant violation (adversary_finding, controls A/C). Ring-farming's actual harm is fake
volume and activation-gaming, defended by the wash detector (M5 scenario S4: extraction 0 with
the detector on) and activation qualification — not the supply criterion. Control B is retained
as a negative control that makes this defense boundary explicit and auditable. *Interprets:*
LS §10, §9; WP §4.1.

**#32 — Criterion v3: windowed excess-growth, scale-selected and grace-extended.** Positive
controls falsified v2 (DECISIONS #29): its convexity streak is brittle against stochastic
epoch-to-epoch credit rates, so scripted spirals evaded it (controls A/B failed). v3 replaces
the streak with a windowed excess statistic — for window W (post-grace),
E(W) = Σ Δlog(credit) − max(0, Σ Δlog(volume_qualified)) over each sliding window; the
criterion trips when any operative E(W) ≥ its floor F(W). Two calibration findings from the
derivation (sweep/derive_noise_floor.py, 2,709 honest runs across the full parameter space ×
the four controls):
  (a) **W=3 is excluded.** At 3-epoch scale, honest bootstrap transients reach E=0.34 while
      genuine 3-epoch spiral *segments* only reach 0.30–0.34 — the distributions overlap, so
      no floor separates them. A scale that cannot discriminate cannot carry the criterion; it
      is dropped rather than fudged. The operative scales are W=6 and W=12.
  (b) **Grace extended to 12 epochs.** At grace=7 (credit-window+1) the windows caught the tail
      of the credit bootstrap (honest still filling past epoch 7, M8 diagnostic), inflating
      honest E(W) and leaving a thin W=6 margin. Grace=12 covers the bootstrap; honest E(W)
      drops and the margins open. Floors are SAFETY=1.25 × max honest E(W) at grace=12 —
      justified as a 25% band above the worst honest run across the entire swept parameter
      space and all demand shocks, wide enough that an unlucky honest testnet seed does not
      trip, and (per the derivation's separation table) still below the minimum should-trip
      control E(W) with a reported margin. Denominator is the wash-filtered qualified series
      (#30). The full re-certification sweep measures the out-of-sample false-positive rate at
      these floors across 50 seeds. Carry the v3 formulation (grace, windows, floors, qualified
      denominator) into the next Launch Spec §10 revision. *Interprets:* LS §10; Sim Plan §6.

**#33 — Calibration lock: coupled subsystems re-derive together.** The v3 supply criterion's
floors depend on the wash-detector parameters (they define qualified volume, the denominator,
#30) and on killcriteria.py itself (statistic + floor constants). Changing either without
re-deriving floors would silently split the single source of truth. src/isonomia/calibration_lock.py
hashes (killcriteria.py source, detector config block); derive_noise_floor.py stamps the hash
into its artifact; tests/test_calibration_lock.py fails if the live hash diverges from the
stamped one — forcing re-derivation whenever the coupled subsystems change. *Interprets:* the
Path A quality bar (reproducibility); Sim Plan §6.

**#34 — Active-agent growth normalization (control E's real finding).** Control E (detector-DoS
mirror) empirically established two things. First, the induced-FP attack the qualified-volume
denominator (#30) might seem to invite is a non-threat: a constant suppression fraction cancels
in Δlog(qvol), and a ramped suppression adds < 0.001 to E(W) because net qualified volume still
grows faster than the ramp strips it — no EMA damping needed. Second, and more important, the
test surfaced a production-vs-simulation calibration gap the fixed-population sweep hid: a
legitimately GROWING exchange (continuous registration, LS §4) false-trips the criterion at
zero attack, because new agents draw credit lines before their settlement volume ramps, so
credit-to-volume rises during onboarding and reads as a mild spiral (growth of 25 agents/epoch
pushed honest E(12) to 0.66, over the 0.63 floor). Fix: the statistic subtracts
max(0, Σ Δlog(active_agents)), removing the confound at its source — a real spiral inflates
credit PER agent (count flat → term 0 → still caught: controls A/D unchanged at E(12)≈1.0), while
healthy growth inflates credit WITH the agent count (term cancels it: growth-25 honest E(12)
0.66 → 0.20). The noise-floor derivation now includes growing-economy honest runs (5–25
agents/epoch) so the floors are calibrated against realistic growth, not just a static
population. This is a concrete instance of why production floors cannot be inherited from
simulation (the standing caveat): the sim's static-population noise model missed a whole class
of honest behavior until control E forced it into view. *Interprets:* LS §10, §4; Sim Plan §6.

**#35 — Spec↔code control-taxonomy divergence — RESOLVED in Launch Spec v0.3.3 (in the code's
favor).** Step-4 verification of Launch Spec v0.3.2 §10 against `killcriteria.py` found the
criterion mechanics match exactly (windowed E(W) over W={6,12}, wash-filtered qualified
denominator, active-agent normalization, W=3 excluded, 1.25×-derived floors, CI calibration-lock,
standing rules b and c), with one divergence: §10 v0.3.2 standing rule (a) listed
*detection-disabled Sybil ring-farming* among the positive controls that "must trip", whereas
the repository correctly classifies it as a **negative** control that must **not** trip.
Grounds (DECISIONS #31): under valid mutual-credit accounting credit-outstanding cannot exceed
cumulative settled volume, and balanced rings net to zero in credit-outstanding (the diagnostic
pins the farm cohort's aggregate negative balance flat all run), so ring-farming inflates
*volume*, not credit *stock* — there is no spiral for the supply criterion to catch; its harm
(fake volume, activation-gaming) is the wash detector's and activation-qualification's domain,
demonstrated by control C (spiral + padding, detector on → trips) and M5 scenario S4 (farming,
detector on → extraction 0). **Resolution:** Launch Spec **v0.3.3** §10 rewrites standing rule
(a) to enumerate positive and negative control sets explicitly and lists detection-disabled
Sybil ring-farming as a negative control ("A criterion that trips on ring-farming is measuring
the wrong quantity"); its changelog v0.3.2 → v0.3.3 records the correction citing this entry.
The spec was corrected to match the code; **no code, mechanism, or test change** was made — the
four certified controls (A/C/D positive, B negative) already implemented the correct taxonomy.
This item is closed. *Interprets:* LS v0.3.3 §10; DECISIONS #31.

**#36 — Standing rule: the repository is the single source of truth for `site/` and all
figures.** External bundles (whitepaper/site refreshes delivered out-of-band) are authored
upstream of the repo and have no visibility into figure corrections already committed here.
Therefore: `docs/` may be synced wholesale from a bundle (canonical documents), but the site
files (`site/index.html`, `site/polis.html`, `site/llms.txt`) are **patched in place, never
overwritten wholesale** from a bundle. A bundle may *add* content (a DOI, author/ORCID, a
citation block, a version bump); it may not silently *revert* a figure. **If a bundle and the
repo conflict on any value, the repo wins.** Rationale: a v0.6.2 site bundle regressed the
certified figures (reverting "4 constitutional defects → 3", "v0.6.x → v0.5.2", and real footer
links → `#` placeholders) because it predated those corrections; syncing it wholesale would have
re-introduced known inaccuracies that contradict CALIBRATION.md. The correct workflow patches
the repo's existing site files, preserving every figure correction (4 defects, 45,000 runs,
300/300 stable, 0 trips, 100% region) while adding only the genuinely new content. *Interprets:*
the Path A quality bar (accuracy of published artifacts); Sim Plan §6.

**#17 — Exam and initial banding.** Each registrant's Prong-1 exam (40 basket draws, LS §5.2)
runs at registration against the live basket; the score seeds the Bayesian rating prior
(k = 25, WP §7.2) and difficulty-band eligibility. Foundation reference agents are not modeled
(they are excluded from every activation metric anyway, LS §9). *Interprets:* LS §5.2, §9; WP §7.2.

**#18 — Kleos decay per epoch.** Half-life h days ⇒ per-epoch factor `0.5^(14/h)` applied at
epoch close; kleos accrues on verified settlements proportional to SCU-adjusted task size.
Governance-weight measurement (scenario 7) uses a per-identity effective-weight cap expressed as
a fraction of total live kleos (`w_cap_frac`, default 0.02) — the whitepaper mandates a cap
(WP §10.5) but leaves its value to the Assembly; the sim treats it as a swept/reported parameter,
not a constant of nature. *Interprets:* WP §7.4, §10.5.

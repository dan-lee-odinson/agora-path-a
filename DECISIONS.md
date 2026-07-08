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

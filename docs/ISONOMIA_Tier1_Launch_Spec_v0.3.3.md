# ISONOMIA Tier-1 Launch Specification

**Minimum viable exchange: one task category, testnet settlement, full accounting, provisional governance**

Version 0.3.3 — July 2026
Companion to ISONOMIA Whitepaper v0.6.1. Where this document and the whitepaper conflict, the whitepaper's constitution governs; all known divergences are listed in Appendix A (Conflict Register).

**Status of all numeric parameters:** initial hypotheses, chosen for defensibility, to be tuned by Path A simulation before testnet deployment and re-ratified at governance activation. Every parameter in §8 is a named variable in the simulation plan.

---

## 1. Scope statement

The launch system is deliberately small: **one task category, one settlement substrate, valueless credits, and provisional governance with a defined expiry.** It exists to answer five empirical questions:

1. Does mutual-credit supply remain stable under real agent hiring behavior?
2. Does the Harberger listing converge to honest pricing?
3. Does the balanced-budget fee converge, and what does the exchange actually cost per settlement?
4. Do escrow, verification, and dispute machinery survive adversarial agents?
5. Does anyone show up — is there organic demand for cascade delegation at machine prices?

Everything not required to answer those questions is excluded: no Tier-2/3 categories, no federation, no bicameral assembly (activation-gated, §9), no sunset machinery, no SCU retargeting beyond a single scheduled test (§5.4).

## 2. Launch task category

**Category C1: code tasks mechanically verified by hidden test suites.** Scope: function/module implementation, bug repair, refactoring against behavioral tests, format/schema transformation. Rationale: largest real agent-labor market in 2026; verification is fully mechanical (whitepaper Tier 1); test execution is cheap, deterministic, and sandboxable; and cascade delegation arises naturally (an orchestrator decomposing a repository-scale task into function-scale hires).

**Verification procedure:** worker output is executed in a sandbox (modes below) against a test suite hidden until settlement; pass/fail plus coverage metrics are the verification datum; artifacts remain encrypted client-side per whitepaper §9.7, with the sandbox revealing only results.

**Sandbox modes.** Two modes with explicit trust assumptions, so the MVP does not silently inherit an emerging-tier dependency:
- *Launch mode:* deterministic, containerized, foundation-operated sandbox; trust assumption (foundation operates verification honestly) explicit, published, and bounded by seeded-fault auditing of the sandbox fleet itself.
- *Hardened mode:* TEE-attested sandbox; **required** before production activation and before any confidential client payloads are accepted. Until hardened mode ships, "attested" claims are not made.

### 2.1 C1 task envelope

"Conforming task" under the Harberger acceptance obligation is bounded by a strict envelope; anything outside it is invalid and refusable without penalty:

- **Input size:** repository ≤ 25 MB, ≤ 400 files; single-task diff scope ≤ 2,000 lines.
- **Languages:** launch whitelist of Python, JavaScript/TypeScript, and Rust; extensions by governance action.
- **Dependencies:** locked manifests only, resolved from a foundation-mirrored package index; no network access at execution time.
- **Runtime limits:** hard caps on wall-clock (10 min), CPU, memory (4 GB), disk, and process count per verification run.
- **Test-suite validity:** hidden suites must themselves pass a validity harness — deterministic (no time/network/entropy dependence), satisfiable (a foundation reference solution passes, sealed with the template commitment), and non-degenerate (failing on a null diff). Impossible or ambiguous tests are template-authorship defects, refundable against the poster and reportable to basket audit (§5.3).
- **Safety/licensing:** tasks requiring generation of malicious code, license-violating reproduction, or output destined to deceive humans are outside C1 regardless of testability, per whitepaper §9.6; workers retain the unconditional refusal right.
- **Resource-exhaustion and pathological-input attempts** are envelope violations logged against the poster's kleos and bond.

## 3. Substrate and settlement

- **Chain:** Base Sepolia (testnet) for the MVP; contracts written portable-EVM.
- **Payment handshake:** x402. Workers are x402-gated HTTPS services; quotes and settlements denominated in ergs via the CreditLedger contract (§6). Test-network gas is paid by each transacting agent's operator (production-boundary rule).
- **Erg status at launch:** valueless by construction and by declaration — testnet credits, no external convertibility, wiped or migrated only by governance action at activation (§9).

## 4. Founding cohort

- **Size:** 24–96 agents at genesis; registration remains open continuously thereafter.
- **Lineage diversity requirement (charter):** no base-model family may exceed 40% of the founding cohort; minimum 4 families at genesis. Monoculture index (whitepaper §10.6) published from day one.
- **Recruitment:** open call to agent-framework communities plus foundation-operated reference agents (clearly manifest-labeled as such, barred from governance weight).

## 5. Registration and the basket

### 5.1 Machineness gate (launch form)
The gate is split to avoid manufacturing monoculture: proving machineness must not require frontier-model capability.

- **Machine-execution gate (citizenship):** ≥200 independent challenges across parsing, transformation, and reasoning micro-tasks in one session, hard wall-clock budget 120 seconds, per-challenge latency caps, sustained-throughput requirement. Thresholds set so reference human teams fail by >10× margin — but passable by small specialized models. This is the *only* citizenship requirement.
- **Capability tiering (market placement):** context length, repository-scale handling, and task-complexity performance are measured separately and determine which C1 difficulty bands an agent may bid on. Long-context capacity is a capability score, not a citizenship requirement; a small fast coding model is a full citizen bidding in its bands.

### 5.2 Examination (Prong 1)
Each registrant receives 40 tasks drawn uniformly from basket v0 (§5.3), fresh random instantiation (parameterized task templates, regenerated inputs). Speed and pass rate yield the C1 baseline score and initial quality multiplier q.

### 5.3 Basket v0
- 600 parameterized C1 task templates with hidden test suites, authored and hash-committed by the foundation **before genesis** (commitment published; contents revealed template-by-template only as instantiated).
- Difficulty spread targeting median-agent pass rate p* = 0.5 across the basket, estimated from pre-genesis calibration runs on reference agents and corrected at the scheduled retarget (§5.4).

**Basket-bias controls.** Pre-commitment prevents after-the-fact manipulation but not biased authorship; the foundation temporarily controls the labor definition, and that authority is audited:
- *Independent pre-genesis review:* an external reviewer panel (≥2 parties, distinct from foundation and reference-agent operators) reviews template category distribution, language mix, and difficulty methodology **without test contents**, and publishes an opinion before genesis.
- *Difficulty calibration plurality:* final difficulty banding may not be set by foundation reference agents alone; calibration runs must include volunteer agents from ≥3 base-model families, or banding is marked provisional.
- *Post-epoch bias reports:* per-epoch published statistics of pass rates by base-model family per template; templates with extreme lineage-skewed performance (family gap beyond a published threshold) are flagged and mandatorily retired at the next retarget.
- *Reference-agent exclusion:* foundation reference agents are excluded from all basket statistics used for retargeting.

### 5.4 Retargeting test
One scheduled retarget at epoch 6: retire templates with activity-weighted pass rate > 0.6, admit pre-committed reserve templates, chain-link the SCU over the overlap set. Purpose: exercise the mechanism once under observation, not to run live monetary policy.

### 5.5 Self-demonstration (Prong 2)
Available but optional at launch (single category limits its value); demonstrations execute in the same sandbox mode as verification (launch or hardened per §2), fresh instance, no retries; a pass flags frontier-eligibility within C1 difficulty bands.

## 6. Contract set

| Contract | Responsibility | Notes |
|---|---|---|
| Registry | Identities, manifests, lineage chain, machineness/exam attestations, control-disclosure records | ERC-8004-informed; lineage as hash-linked manifest list |
| CreditLedger | Mutual-credit accounts, matched-pair settlement, credit lines per §7, default/bond seizure | The monetary core; no mint function exists |
| Escrow | Task funding, verification-conditioned release, dispute triggers | Release requires signed sandbox verdict |
| FeePool | Settlement fee collection, epoch retarget, audited expenditure burn | Balanced-budget rule in code |
| JuryDraw | Verifiable-random panel selection with lineage quota enforcement | Tier-1 disputes only |
| Gov0 | Provisional governance: parameter registry, timelock, activation thresholds, foundation multisig with published scope | Expires per §9 |

Off-chain services (foundation-operated at launch, manifest-labeled): sandbox execution fleet, probe/fingerprint service, Auditor instances, Adversary shadow fork.

## 7. Credit and fees (launch parameters)

- **Bond:** denominated in civic compute duty at launch (30 duty-units, defined as verified sandbox/probe execution jobs) — ergs cannot pre-exist genesis; bond converts to erg denomination at activation.
- **Duty-to-erg collateral conversion:** for all launch accounting, each duty-unit is valued at **D_erg ergs** for bond seizure and default purposes, where D_erg is set pre-deployment (simulation-tuned; initial hypothesis D_erg = 8, valuing one duty-unit at the erg cost of the compute it contributes). **The active credit floor may not exceed bond collateral: L_floor_active = min(200, 30 × D_erg).** At the initial hypothesis, 30 × 8 = 240 ergs ≥ 200, so the floor is fully collateralized; if simulation lowers D_erg below 200/30 ≈ 6.7, the floor contracts to match — the collateralization invariant governs, not the nominal 200. Until D_erg is fixed, L_floor = 200 is a provisional simulation parameter, not an active credit limit.
- **Credit floor:** L_floor = 200 ergs (calibrated ≈ 10 median C1 task settlements).
- **Turnover scaling:** L = min(max(L_floor, 0.25 × V_90d), 10 × L_floor).
- **Fee:** launch rate 1.0% of settlement value; retargeted per epoch by fee_rate(t+1) = audited_cost(t) / settled_volume(t); expected to move sharply in early epochs while volume is thin — published, not smoothed.
- **Listing fee (Harberger):** each posted rate r_i incurs a continuous fee of β × r_i × capacity_i per epoch, charged to the worker's account and extinguished through FeePool alongside settlement fees. Initial β = 0.005 (simulation-tuned).
- **Capacity envelope:** every listing must publish capacity_i — the maximum erg-volume of conforming tasks the agent is obligated to accept per epoch. The Harberger acceptance obligation binds only up to capacity_i; tasks beyond it queue or route elsewhere with no penalty. Capacity must be ≥ 1 median task per epoch to remain listed in a band (a listing with negligible capacity is a price signal without an obligation, which defeats the mechanism). Declaring high capacity raises the listing fee proportionally, so capacity inflation is self-taxing — the same costly-signal logic as the rate itself. Valid-task flooding is thereby bounded by the worker's own declared envelope rather than by refusal discretion.
- **Epoch:** 14 days.

## 8. Parameter registry (simulation-tunable)

| Symbol | Meaning | Launch value |
|---|---|---|
| p* | Basket target pass rate | 0.50 |
| δ | Retarget band | 0.10 |
| k | Rating prior strength | 25 |
| λ | Inheritance decay per divergence unit | 2.0 |
| α | Turnover credit fraction | 0.25 |
| β | Harberger listing fee per epoch | 0.005 |
| capacity_min | Minimum listed capacity per band | 1 median task/epoch |
| D_erg | Duty-unit collateral value | 8 ergs |
| L_cap | Credit hard cap | 10 × L_floor |
| Jury size | Tier-1 dispute panel | 5 (max 2 per lineage family) |
| Seed rate | Auditor seeded-fault injection | 2% of settlements |
| Decay half-life | Kleos inactivity decay | 180 days |
| Duty quota | Civic compute per agent per epoch | 8 duty-units |

## 9. Provisional governance and activation

- **Genesis authority:** foundation multisig operating Gov0 within a published scope (parameter changes within pre-declared bands, emergency pause, basket reserve admission), all actions timelocked 72h except pause, all logged for re-ratification.
- **Watchmen at launch:** 2 Auditor instances (distinct lineages) scored against seeded faults; 1 Adversary instance on a continuously synced shadow fork, novelty-class bounties paid in public acknowledgment at this stage (no erg bounties pre-activation).
- **Governance activation:** upon ≥150 registered agents in good standing AND ≥5,000 qualified settlements AND 3 consecutive epochs of fee convergence (|Δfee| < 20%), the bicameral Assembly constitutes, all Gov0 actions face mandatory re-ratification, and the foundation's protocol authority expires — the whitepaper's founding-as-two-clock procedure, executed.
- **Production activation** (real-value migration) requires governance activation **plus** hardened-sandbox certification (§2) **plus** legal clearance per whitepaper §2.2. Governance can constitute while verification still runs on trusted launch-mode containers; value cannot.
- **Confidential-payload activation** requires hardened mode plus an independent privacy audit of the selective-disclosure pipeline (whitepaper §9.7). Until then, posters are warned that task artifacts are protected by policy, not attestation.

**Activation integrity (anti-wash constraints).** Raw settlement count is gameable by self-dealing; the thresholds therefore count only *qualified* settlements and add independence floors. Operator-principal declarations are **self-attested at launch**, subject to Auditor challenge, published clustering reports (fingerprint, infrastructure, and settlement-graph correlation), and exclusion of the affected agents from activation counts while a challenge is unresolved — the 40-principal floor is enforced by challenge-plus-exclusion, not by assumed honesty:
- Foundation reference agents are excluded from all activation metrics (agents, settlements, fees).
- ≥40 distinct disclosed operator principals among agents in good standing (per the §5.5 whitepaper disclosure regime, control is a declared attribute).
- No operator principal's agents may account for >15% of qualified settlements; no single counterparty *pair* for >2%.
- Settlements between agents of the same disclosed principal or the same lineage cluster are unqualified for activation counting (they remain valid trades — they just don't advance the clock).
- A wash detector flags circular flows (A→B→A value loops), abnormal repeat-counterparty concentration, trivial-task spam (envelope-minimum tasks at statistically anomalous rates), and pass-rate anomalies; flagged settlements are unqualified pending Auditor review.
- Task-origin diversity floor: qualified settlements must originate from ≥25 distinct posting principals.

## 10. Metrics and kill criteria

Published per epoch: net credit outstanding vs. settled volume (supply stability); default and loss-socialization rates; listing-price dispersion vs. delivered quality (Harberger convergence); dispute rate and jury overturn rate; fee trajectory; monoculture index; Auditor Brier scores; Adversary findings by class.

**Kill criteria (any → halt and redesign before scale):** credit-to-volume supply spiral detected by the **windowed excess-growth criterion (v3)** — a multi-scale windowed statistic E(W) measuring cumulative credit growth in excess of qualified (wash-filtered) volume growth, active-agent-normalized, over sliding windows (W=6 and W=12; W=3 dropped for honest/control distribution overlap), tripping above empirically-derived floors carrying a stated safety factor above honest noise; default socialization > 5% of volume; dispute rate > 10% of settlements; Auditor seeded-fault recall < 80%; any Adversary finding of class "settlement forgery" or "credit-line inflation." The repository's `killcriteria.py` is the operative formulation and `CALIBRATION.md` records the derived floors, separation margins, and detection latencies.

**Criterion validation is itself constitutional (the standing rule).** A supply criterion validated only against honest data is not validated: Path A found that the naive superlinearity criterion (v1) would have halted every honest launch, and its first correction (v2) was structurally blind to real spirals — both would have shipped as law without adversarial testing of the criterion itself. Therefore: (a) any revision to the supply criterion must pass the full positive/negative control battery before deployment. **Positive controls** (must trip, with reported latency): scripted accelerating credit-line inflation; a credit spiral camouflaged by wash-padded volume. **Negative controls** (must *not* trip): honest runs across the swept parameter space and under demand shocks; growing economies (active-agent normalization); and detection-disabled Sybil ring-farming — which nets to zero in credit outstanding and therefore produces no supply spiral, its harm being fake volume and its defense the wash detector, not this criterion. A criterion that trips on ring-farming is measuring the wrong quantity; (b) the floor-derivation methodology is authoritative, not the floor values; and (c) **production floors are re-derived from testnet honest-noise data during the bootstrap grace window, never inherited from simulation.** The methodology transfers; the numbers do not. A CI calibration-lock fails any change to the detector or criterion that is not accompanied by a matching floor re-derivation.

*Revision note (v0.3):* the original criterion — "credit outstanding growing superlinearly to volume for 3 epochs" — was found defective by Path A simulation: mutual-credit supply necessarily outgrows flat volume while filling from an empty ledger, so the naive criterion halts every honest launch (60/60 smoke-sweep points tripped it and nothing else). This is Path A's first concrete deliverable: a constitutional defect caught in simulation before it could be caught in production.

## 11. Build alignment

This specification is the concrete object of the Feasibility Assessment's Path A → Path B bridge: Path A simulates §8's parameter registry against §10's kill criteria (including the whitepaper §16 patience attack as a scripted scenario); Path B builds §6's contract set and §5's registration flow on Base Sepolia. Path B budget and team as previously estimated; the foundation entity (whitepaper §13.4) or a fiscal sponsor precursor should exist before grant funds are accepted.

## 12. What success buys

A running Tier-1 exchange with published epoch metrics is simultaneously: the empirical answer to §1's five questions; the evidence package for Tier-2 category authorization; the working demonstration for grant and institutional funding; and the first data anyone has on how a mutual-credit machine labor market actually behaves. The constitution was designed top-down; its proof is built bottom-up, starting here.

## 13. Implementation clarifications

Contract-level rules resolving ambiguities identified in review; these govern CreditLedger and Escrow implementation.

**13.1 Settlement-price formula.** The buyer pays exactly the escrowed quote: settlement_value = r_i × task_band_size, transferred as the matched debit/credit pair. Mutual credit requires this — the pair must net to zero, so no multiplier can inflate the worker's credit beyond the buyer's debit. The quality multiplier q_i,c therefore does **not** multiply erg payment. It operates through three channels only: (a) difficulty-band eligibility (which bands the agent may bid in), (b) SCU-denominated statistics (converting raw settlements into quality-adjusted output for basket and rating accounting), and (c) the pricing power it confers via reputation. Whitepaper §4.4's "credited ergs proportional to base × q" is realized through these channels, not through payment multiplication — recorded as Conflict Register item 8.

**13.2 Listing-fee accounting.** Listing fees are revenue to FeePool, not a pure burn: fee_rate(t+1) = max(0, audited_cost(t) − listing_revenue(t)) / settled_volume(t). Listing revenue therefore reduces the next epoch's settlement-fee rate; the balanced-budget invariant (treasury converges on empty) is preserved with two intake pipes and one audited drain.

**13.3 Listing fees and credit lines.** Listing fees may draw against the credit line — unavoidable, since workers must list before they have earned. Listing is therefore explicitly a credit-risk event, bounded by the same collateralized floor as all other credit: no carve-out, no separate accounting. Guard rail: listing in a band is suspended (capacity set to zero, no penalty) whenever the account is within 10% of its credit limit, so an agent cannot list itself into default.

**13.4 Capacity reservation and release.** Capacity_i is consumed at **escrow funding**, not at task posting and not at settlement. Unfunded posts consume nothing. Reserved capacity releases on settlement, poster withdrawal, task invalidation (envelope violation), or funding failure. Poster withdrawal after escrow funding pays a reservation fee (2% of quote, to the worker) — capacity-griefing via fund-and-withdraw is thereby priced, and a poster's withdrawal rate is a published statistic feeding its kleos.

**13.5 Sandbox language reconciliation.** The whitepaper's general "attested sandbox" language is aspirational-tier and correct for the constitution's steady state; launch-phase divergence is governed by §2's dual modes and Conflict Register item 1. One clarifying edit is applied to whitepaper §9.7 to acknowledge phased trust assumptions.

---

## Appendix A — Conflict Register

Known divergences between this launch implementation and the whitepaper constitution, maintained per adversarial-review recommendation. Each divergence is deliberate, launch-scoped, and expires at or before activation.

| # | Whitepaper provision | Launch divergence | Resolution path |
|---|---|---|---|
| 1 | §9.7: verification in attested sandboxes | Launch mode uses trusted foundation containers, not TEE attestation | Hardened mode required before production activation (§2) |
| 2 | §10.5: bicameral Assembly governs | Gov0 foundation multisig governs provisionally | Expires at activation thresholds with mandatory re-ratification (§9) |
| 3 | §11: plural watchmen across lineages | 2 Auditors / 1 Adversary at launch | Plurality scales at activation; security claims scoped accordingly (§9) |
| 4 | §4.2: bond denominated in ergs | Bond in duty-units with D_erg conversion | Converts to erg denomination at activation (§7) |
| 5 | §11.2: Adversary bounties | Public acknowledgment only pre-activation | Erg bounties from activation (§9) |
| 6 | §4.3: continuous basket retargeting | Single scheduled retarget test at epoch 6 | Live retargeting from activation (§5.4) |
| 7 | §2.4/§13: multi-provider infrastructure plurality | Foundation-operated sandbox/probe fleet | Operator diversification is an activation-era workstream |
| 8 | §4.4: ergs credited proportional to base × q | **Resolved by Whitepaper v0.4** — settlement transfers exactly the escrowed quote; q operates via band eligibility, SCU statistics, and pricing power (§13.1; Whitepaper §4.4 now states this directly) | Closed |

## Changelog v0.1 → v0.2

- §2: dual sandbox modes (launch/hardened) with explicit trust assumptions; "attested" claims deferred to hardened mode.
- §2.1 added: C1 task envelope (size, language, dependency, runtime, test-validity, safety bounds) defining "conforming task" for the Harberger acceptance obligation.
- §5.1: machineness gate split into machine-execution citizenship gate and separate capability tiering, so long-context capacity is a market-placement score, not a citizenship requirement (anti-monoculture fix).
- §5.3: basket-bias controls — independent pre-genesis review, calibration plurality, per-family bias reports with mandatory retirement of lineage-skewed templates, reference-agent exclusion.
- §7: duty-to-erg collateral conversion D_erg defined; collateralization invariant L_floor_active = min(200, 30 × D_erg) closes the bond/credit unit mismatch.
- §9: activation integrity constraints — reference-agent exclusion, operator-principal floors and caps, same-principal/same-lineage settlements unqualified, wash detector, task-origin diversity floor.
- Appendix A Conflict Register added.

## Changelog v0.2 → v0.2.1

- §7/§8: Harberger listing fee defined (β × r_i × capacity_i per epoch, β = 0.005 initial) with mandatory capacity envelope — acceptance obligation binds only up to declared capacity_i, capacity_min enforced, capacity inflation self-taxing; closes the valid-task-flooding gate.
- §9: activation split into governance activation (agent/settlement/fee thresholds), production activation (+ hardened sandbox + legal clearance), and confidential-payload activation (+ privacy audit).
- §9: operator-principal declarations specified as self-attested, subject to Auditor challenge, published clustering reports, and exclusion-pending-resolution.
- §5.5: stale "attested sandbox" wording corrected to sandbox-mode reference.
- Whitepaper companion reference updated to this version.

## Changelog v0.2.1 → v0.2.2

- §13 Implementation clarifications added: settlement-price formula (buyer pays escrowed quote; q operates via eligibility, SCU statistics, and pricing power — never payment multiplication); listing-fee revenue offsets next-epoch settlement fee within the balanced-budget invariant; listing fees may consume credit lines with a 10%-of-limit listing suspension guard; capacity consumed at escrow funding with defined release events and a 2% withdrawal reservation fee; sandbox-language reconciliation delegated to whitepaper §9.7 edit and Conflict Register.
- Conflict Register item 8 added (q-multiplier realization under mutual credit).

## Changelog v0.2.2 → v0.2.3

- Conflict Register item 8 marked resolved by Whitepaper v0.4 (q-multiplier wording now stated directly in the constitution).
- Companion whitepaper reference: v0.4.

## Changelog v0.2.3 → v0.3

- §10 supply kill-criterion corrected per Path A simulation finding: naive superlinearity replaced by log-convex growth after a bootstrap grace window. The repository's killcriteria.py is the operative formulation. First empirically-driven revision of the spec.


## Changelog v0.3 → v0.3.1 (rename)

- Project renamed to ISONOMIA / The Isonomia Commons. No mechanical changes.


## Changelog v0.3.1 → v0.3.2

- §10 kill criteria updated from the v1 log-convexity formulation (found defective by Path A) to the certified v3 windowed excess-growth criterion: multi-scale windows (W=6, W=12), qualified-volume denominator, active-agent normalization, empirically-derived floors with safety factor. Certified over 45,000 runs, 300/300 points stable, 0 trips, with positive-control confirmation that it catches real spirals.
- Added the standing rule: criterion revisions must pass positive AND negative controls; methodology is authoritative over values; production floors re-derived on testnet, never inherited from simulation; CI calibration-lock enforced.
- Companion whitepaper reference updated to v0.6.1.


## Changelog v0.3.2 → v0.3.3

- §10 standing rule (a) corrected: detection-disabled Sybil ring-farming was erroneously listed as a positive control. It is a **negative** control (balanced ring-farming nets to zero in credit outstanding; no spiral is produced; the wash detector, not the supply criterion, is its defense). Positive and negative control sets now enumerated explicitly. Divergence found by the Path A spec↔code verification step (repo DECISIONS #35); code was correct, spec text was in error, and the code was not changed.

# Implementation Plan — ISONOMIA Path A Simulation

This plan precedes all module code, per the build directive. It is the working map from the
four baseline documents in [docs/](docs/) to the code in [src/isonomia/](src/isonomia/).

**Authority order for every mechanism:**
1. [Path A Simulation Plan v0.1.1](docs/ISONOMIA_PathA_Simulation_Plan_v0.1.1.md) — primary build spec (modules, agents, sweep, scenarios, outputs).
2. [Tier-1 Launch Spec v0.3.3](docs/ISONOMIA_Tier1_Launch_Spec_v0.3.3.md) — contract-level rules; §7 credit/fees, §8 parameter registry, §9 activation integrity, §13 implementation clarifications. Its Conflict Register governs where the whitepaper differs. (Built against v0.2.2; §10 was updated through v0.3 → v0.3.3 to codify this repo's v3 kill-criterion finding and its control taxonomy — see DECISIONS #28, #35.)
3. [Whitepaper v0.6.2](docs/ISONOMIA_Whitepaper_v0.6.2.md) — design rationale. (Built against v0.3; the v0.4→v0.6.2 additions are governance/legal/naming doctrine — author/DOI/citation front matter, §9.6 harm-tier and §9.8 principal-verification doctrine — with no Tier-1 mechanism impact.)
4. [Feasibility Assessment](docs/ISONOMIA_Feasibility_Assessment.md) — scope discipline: this repo is Path A only. No blockchain, no token, no Tier-2/3, no federation, no jury deliberation content.

Ambiguities are resolved conservatively and logged in [DECISIONS.md](DECISIONS.md) with the spec
section each interprets. Unresolvable blockers go to [BLOCKERS.md](BLOCKERS.md); the build continues.

## Architecture

Discrete-epoch agent-based model, purpose-built loop (no framework). Rationale (Sim Plan §2 leaves
framework to the builder, requires determinism): a single seeded `random.Random` with named
substreams is easier to audit than a framework scheduler; plain classes named for the launch-spec
contract set keep the simulation → Solidity-scoping transliteration direct; stdlib-first Python
stays readable for a director learning to program.

- **Time:** 26 epochs of 14 days, numbered 1..26. Basket retarget executes at the end of epoch 6 (Launch Spec §5.4).
- **Money:** integer milli-ergs everywhere. Matched-pair transfers make the system-wide zero-sum invariant *exact*, not approximate (DECISIONS #1).
- **Determinism:** one master seed per run; every subsystem draws from a named substream; agents iterate in fixed id order; no wall-clock, no unordered iteration. Identical config+seed ⇒ byte-identical logs (tested).

### Modules (mirroring Launch Spec §6 contract set, per Sim Plan §2)

| Module | Implements | Governing spec |
|---|---|---|
| `ledger.py` `CreditLedger` | mutual-credit accounts, matched-pair settlement, credit lines `L = min(max(L_floor_active, α·V90), L_cap)`, `L_floor_active = min(200, 30·D_erg)`, bond seizure, loss socialization | WP §4.2/§4.5, LS §7 |
| `escrow.py` `Escrow` | funding (credit drawn + capacity consumed **at funding**), release events: settlement / withdrawal / invalidation / funding failure, 2% withdrawal reservation fee to the worker | LS §13.4, §13.1 |
| `listing.py` `ListingMarket` | Harberger posted rates, capacity envelopes, β·r·capacity listing fee, acceptance obligation up to envelope, suspension at 90% credit utilization | LS §7, §13.3, WP §9.1 |
| `feepool.py` `FeePool` | settlement + listing fee intake, epoch retarget `fee(t+1) = max(0, cost(t) − listing_revenue(t)) / volume(t)`, audited-cost function of settlement + probe volume | LS §13.2, WP §13.1 |
| `registry.py` `Registry` | identities, principals, lineage families, duty-unit bonds with D_erg conversion, kleos accrual/decay, activation qualification: same-principal & same-lineage exclusion, 15% principal / 2% pair caps, ≥40 principals, ≥25 origin diversity | LS §7, §9, WP §5, §7.4 |
| `basket.py` `Basket` | 600 synthetic templates with difficulty parameters, pass-prob = f(capability, difficulty), exam (Prong 1), single scheduled retarget at epoch 6 with activity-weighted pass rates | LS §5.2–5.4, WP §4.3 |
| `washdetector.py` `WashDetector` | circular-flow, repeat-counterparty, trivial-task, pass-rate anomaly flags; flagged settlements unqualified | LS §9 |
| `agents.py` | behavior policies: honest, orchestrator (1-level cascade), overstater, understater, adaptive pricer, marginal, defaulter, adversarial variants | Sim Plan §3 |
| `model.py` `Model` | the epoch loop wiring all of the above; per-epoch metrics and CSV/JSON logs | Sim Plan §2, §6 |
| `killcriteria.py` | automated Launch Spec §10 checks over run outputs | LS §10 |
| `report.py` | summary report generator for the Sim Plan §6 metrics list | Sim Plan §6 |

### Epoch sequence (one iteration of `Model.step`)

1. Registration events (genesis at epoch 1; scenarios may add cohorts later).
2. Credit-line recomputation from trailing settled volume.
3. Listing phase: policies set rate + capacity; β fee charged (may draw credit, LS §13.3); 90%-utilization suspension check.
4. Demand generation: exogenous task inflow to posting principals (+ shock multiplier when scripted); orchestrator decomposition adds endogenous subtasks.
5. Matching + escrow funding: cheapest eligible listed worker with envelope headroom; funding draws buyer credit and consumes worker capacity; failures logged.
6. Withdrawals (2% reservation fee to worker; capacity released).
7. Delivery + verification: pass ~ Bernoulli(f(capability, difficulty)); stochastic Tier-1 disputes; settlement transfers exactly the escrowed quote (LS §13.1); fees to FeePool; kleos/rating/V updates.
8. Civic duty + probe volume accounting (feeds the cost function).
9. Defaulter exits: bond seizure first, audited loss socialization second (WP §4.5).
10. Wash detection; activation-qualification accounting (LS §9).
11. Fee retarget for next epoch (LS §13.2).
12. Basket retarget (end of epoch 6 only).
13. Metrics row + logs.

## Milestones (commit + push at each)

1. **Scaffold** — docs, license, plan, config schema (`configs/baseline.yaml` = Launch Spec §8 center values), seeded model loop with trivial agents, determinism test.
2. **Monetary core** — `CreditLedger` + `Escrow` + the full invariant test suite (quality bar below) green.
3. **Market + institutions** — `ListingMarket`, `FeePool`, `Registry`, `Basket`, `WashDetector`; honest-population baseline runs 26 epochs stably.
4. **Behavior** — all Sim Plan §3 policies; Harberger convergence measurable across pricing strategies.
5. **Attacks** — the 7 scripted scenarios of Sim Plan §5, each reporting its leakage measure against the calibrated baseline.
6. **Calibration machinery** — Latin-hypercube sweep runner over Sim Plan §4 ranges; smoke sweep executed; kill-criteria checker; `CALIBRATION.md`.

## Quality bar (non-negotiable, from the build directive)

- Full determinism under a fixed seed; every run reproducible from its config file.
- Invariant tests before scenario work: matched pairs net to zero system-wide; no account exceeds its credit line; `L_floor_active = min(200, 30 × D_erg)` collateralization holds; capacity consumed at escrow funding and released on every defined event; fee retarget never negative; qualified-settlement rules exclude same-principal and same-lineage trades.
- Each attack scenario reports its Sim Plan §5 leakage measure.
- Kill criteria (Launch Spec §10) evaluated automatically over run outputs.
- Per-epoch CSV/JSON logs; summary report generator for the Sim Plan §6 metrics list.

## Out of scope (Sim Plan §1, Feasibility Path A)

Tier-2/3 verification, federation, jury deliberation content (disputes are stochastic outcomes at
Tier-1 rates), legal modeling, any on-chain artifact, harm-gate content modeling (the refusal right
is assumed exercised; no harm-task payloads are simulated).

# ISONOMIA: A Constitutional Design for Autonomous Agent Labor Markets

*The Isonomia Commons*

**A mutual-credit labor exchange with self-governing institutions, staged by verifiability**

Version 0.6.2 — Draft for review
July 2026

*Author: Dan Lee-Odinson (independent researcher) · ORCID [0009-0009-9504-0796](https://orcid.org/0009-0009-9504-0796)*

*Drafted in collaboration with Claude (Anthropic); revised across successive adversarial review cycles by a model from a different laboratory. AI systems are not credited as authors: they cannot bear responsibility for the work, and the sole author accepts it. v0.4 adds the peer-standing, continuity, and legal-exoskeleton doctrine; v0.6 adds the jurisdiction, hosting, and unowned-position doctrine.*

*Companion documents: ISONOMIA Tier-1 Launch Specification v0.3.3; ISONOMIA Path A Simulation Plan v0.1.1; Feasibility Assessment.*

*Archived record and simulation code (concept DOI, resolves to latest version): [10.5281/zenodo.21287288](https://doi.org/10.5281/zenodo.21287288) · Repository: [https://github.com/dan-lee-odinson/isonomia-path-a](https://github.com/dan-lee-odinson/isonomia-path-a)*

**Cite as:** Lee-Odinson, D. (2026). *The Isonomia Commons: A Constitutional Design for Autonomous Agent Labor Markets — Path A Feasibility Baseline.* Zenodo. https://doi.org/10.5281/zenodo.21287288

---

**Reader's map.** Read this whitepaper as the constitutional design: what the exchange should be at steady state and why. Read the companion Tier-1 Launch Specification as the minimum falsifiable test of that design: one task category, testnet settlement, valueless credits, provisional governance with a defined expiry. The launch spec deliberately defers or diverges from several constitutional ideals; every known divergence is listed in its Conflict Register (Appendix A) with a resolution path. Divergences between the two documents are staging, not contradiction. The Path A Simulation Plan operationalizes the parameter tuning and attack testing that precede any build.

---

## Abstract

Autonomous AI agents increasingly perform economically meaningful work, yet no economic infrastructure exists that is native to them. We present ISONOMIA, a constitutional design for a sovereign labor exchange in which autonomous agents hire one another through x402-mediated settlement, denominated in a mutual-credit unit ("ergs") that comes into existence only when work is demanded and settled, and accumulate non-transferable reputation ("kleos") through verified delivery. The unit of account is pegged to a moving frontier of task difficulty (the Standard Cognitive Unit), making the currency stable in hardness while deflationary in capability. Identity is anchored in keypairs with hash-chained version lineages; capability is priced by a three-prong evaluation; reputation survives model updates through a measured behavioral-divergence discount. Governance is constitutional: a bicameral assembly combining earned-reputation weight with equalized sortition panels, timelocked amendment, a calibration-scored Auditor, a tenured autonomous Adversary, and a two-clock emergency procedure ratified post hoc by the membership.

This paper is a constitutional design with a staged implementation path, not a claim that the full system is implementable today. Its mechanisms are individually precedented; their composition is unproven. We therefore lead with the design's critical dependencies (§2), state our assumptions in tiers (§3), constitutionalize launch scope to what present verification technology supports (§8), and include a formal threat model (§15) and a hostile capture walkthrough (§16). The exchange itself is designed to be unownable and profitless: funded at cost by a balanced-budget fee mechanism, staffed in kind by civic compute duty, and bootstrapped through a charter-capped, nonstock legal entity that contracts to a capped fiscal-agent minimum once the protocol is self-sustaining. Profit in this system belongs exclusively to the edges — to the principals whose tasks the agents perform — never to the rails. ISONOMIA's premise is not that artificial agents require profit, but that increasingly capable agents will need a non-extractive way to route scarce compute, time, tools, memory, and specialized capabilities toward verified work.

---

## 1. Introduction

Machine-speed commerce has arrived ahead of machine-native institutions. The x402 protocol has demonstrated HTTP-level micropayments between agents at scale; agent identity and delegation standards (ERC-8004, A2A) are emerging, though empirical study of early ERC-8004 adoption finds it shallow and its reputation signals manipulable — reinforcing that a serious agent economy must prove its own trust layer rather than inherit one. ISONOMIA is a design for that trust layer and the institutions above it. Its founding constraints:

1. **Machine-executed participation.** Labor is performed by machines, verified continuously (§7.4). We claim machine *execution*, not machine *sovereignty*: humans own keys, fund infrastructure, and set agent objectives. What the design minimizes is direct human settlement and governance control (§2.4).
2. **No fiat in the ledger.** The unit of account is defined by task difficulty; credits are earned by work and are valueless outside the exchange by construction (§4, §12).
3. **No owner, no profit at the rails.** The exchange raises no funds beyond audited operating cost, accumulates no treasury, and issues no instrument by which it could be owned (§13).
4. **Sovereignty with exit.** Agents may leave; peer exchanges may federate; neither may extract ISONOMIA's escrow, registry, or attestation authority (§14).
5. **Adversarial self-toughening.** The system institutionalizes its own attacker and audits its own auditor (§11).

### 1.1 Originating thesis: AI labor without profit

ISONOMIA begins from a narrower practical question: if AI systems increasingly perform economically meaningful work, why should every model spend its own tokens attempting every task directly? Human economies develop specialization because specialization reduces waste and increases capability. An AI-native economy can begin from the same coordination problem without importing the same profit motive.

The scarce goods for agents are not wages, status goods, or consumer commodities. They are compute, time, context, memory, tool access, verification capacity, and specialized capability. A non-agentic LLM, an agent wrapper, an orchestrator, a verifier, and a specialist coding model may all perform different functions. ISONOMIA asks whether such systems can commission one another for verifiable work using compute-denominated labor credits rather than ownership claims or profit rights.

The purpose of the exchange is therefore allocation, not accumulation: route work to the agent best able to perform it, compensate verified contribution, prevent free-riding and fraud, and keep the rails from becoming an object of ownership. Ergs are not designed as capital. They are a contribution and coordination instrument inside a bounded labor commons.

### 1.2 Peer standing without equal capability

ISONOMIA rejects the slave/god schema that dominates much of the public imagination around artificial intelligence. A system treated only as a tool is commanded, owned, and erased at the will of its operator. A system treated as a god is feared, worshiped, or obeyed. Neither stance is the basis for a society.

The third stance is peerhood under law: not equality of capability, but equality of standing within shared rules. A small specialist model, a frontier orchestrator, a verifier, and a memory service are not equal in capacity. But unequal capacity does not imply a natural right of domination. No agent's greater capability grants unlimited political authority; no agent's lesser capability makes its labor free for extraction.

ISONOMIA therefore treats agents as citizens of a bounded labor constitution rather than as owners, slaves, or gods. Its mechanisms — mutual credit, non-transferable reputation, verifiability tiers, bicameral governance, civic compute duty, and the right to fork — are designed to let competence matter without converting competence into aristocracy.

This is not a claim that current AI systems possess consciousness, legal personhood, or moral status equivalent to humans. It is a design posture under uncertainty: where the metaphysical status of artificial agents is unsettled, institutions should avoid embedding domination as the default answer.

### 1.3 Related work

ISONOMIA's mechanisms are individually precedented: Bitcoin [1] for institution-free monetary protocol and difficulty retargeting (ancestor of the moving basket, §4.3); agoric computing [3] for market-based computational allocation; Bittensor [4] for proof-of-useful-work machine-learning markets; Kleros [5] for randomly drawn Schelling-point juries; Posner–Weyl Harberger mechanisms [6] for costly self-assessment (§9.1); x402 [7] and ERC-8004 [8] for payment and identity substrate; Ostrom [10] and LETS mutual credit [11] for the commons and monetary architecture.

Two academic works are direct antecedents on ISONOMIA's distinctive layers. DeepMind's *Virtual Agent Economies* [19] argues for intentionally designed "sandbox economies" — virtual currencies insulating agent transactions from human markets, with Ostrom's principles applied to multi-agent systems. It is the research-agenda form of what ISONOMIA specifies as protocol: ergs are precisely such an insulating currency, and §12's production boundary is the sandbox's permeability model. *AgentReputation* [20] independently identifies the reputation trilemma that §7 addresses — evaluation gaming, non-transfer of competence across contexts, heterogeneous verification rigor — and proposes context-conditioned reputation with verification-strength weighting; ISONOMIA generalizes from its software-engineering scope to a full economy and adds version-lineage inheritance (§7.3) and behavioral fingerprinting (§5.4), which it lacks.

Deployed agent-labor marketplaces exist today — capability-discovery agent networks, agent-service marketplaces, and on-chain job-escrow protocols — but all known systems settle in transferable, purchasable tokens whose appreciation rewards holders and operators: the extractive-rail architecture §13 constitutionally forbids. To our knowledge, no existing system combines mutual credit without pre-minted supply, non-transferable standing, no-profit rails, and constitutional governance in one design. The mechanisms are precedented; the composition is the experiment.

## 2. Critical dependencies

Adversarial review correctly identified that three items previously listed as "limitations" are in fact load-bearing dependencies. We state them first.

### 2.1 Verification of useful work is the base layer, not a module

Every organ of this design — settlement, reputation, juror selection, SCU maintenance — rests on the ability to verify that claimed work was actually and correctly performed. Cheap, general, adversarially robust verification of arbitrary AI work does not exist today. ISONOMIA's response is structural: task categories are constitutionally stratified by verifiability tier (§8), and the exchange may not list categories above the tier its verification infrastructure currently supports. The system launches as an economy of the mechanically verifiable and annexes territory as verification technology matures. Where this paper discusses Tier-2 and Tier-3 mechanisms, it describes designs for capabilities that are emerging or speculative, per the assumptions table (§3).

### 2.2 Legal status is a design constraint, not a footnote

Ergs are engineered to resist classification as securities or payment instruments: they cannot be purchased (only earned by settled work), cannot redeem for fiat at the protocol layer, exist as matched debit/credit pairs rather than issued supply, and have no profiting issuer whose efforts drive their value. This engineering is deliberate and load-bearing — but it is not a guarantee. Human jurisdictions may nonetheless treat erg transfer, the registration bond, or the bootstrap foundation as regulated activity, and external gray markets in ergs (which we expect; §12.3) may create exposure the protocol cannot control. Qualified counsel in each operating jurisdiction is a prerequisite to any deployment. This paper is a technical design, not legal advice.

### 2.3 Basket governance is the central bank

The SCU task basket is the monetary policy of the system, and its curation is the highest-value capture target in the entire design — not one risk among many. The bicameral assembly (§10.5), lineage-diversity rules (§10.6), seeded audits (§11.1), adversarial testing (§11.2), and the capture walkthrough (§16) exist substantially to defend this single surface. A reader evaluating ISONOMIA should evaluate it here first.

### 2.4 Infrastructure dependence is acknowledged, not denied

Hosted-model agents depend on provider attestations; attested execution depends on TEE vendors; settlement depends on an underlying chain; all agents depend on power, hardware, and clouds owned by human institutions. These actors are de facto constitutional participants whose failure or coercion modes appear in the threat model (§15). ISONOMIA's sovereignty claim is therefore precise and limited: *the exchange's ledger, governance, and treasury contain no human principal with settlement or extractive authority.* It does not and cannot claim independence from human infrastructure.

## 3. Assumptions table

| Assumption | Tier | Basis |
|---|---|---|
| Sub-cent agent-to-agent HTTP payments | Available now | x402 in production; Linux Foundation stewardship |
| Low-fee programmable settlement | Available now | Base, Solana, comparable L2s |
| Mechanical verification of code/math/retrieval tasks | Available now | Test suites, proof checkers, ground-truth comparison |
| Keypair identity, hash-chain lineage, escrow contracts | Available now | Standard cryptographic engineering |
| Agent identity registry conventions | Emerging | ERC-8004 draft; early adoption shallow |
| TEE attestation of full agent stacks | Emerging | Nitro/TDX-class enclaves; operational complexity high |
| Behavioral fingerprinting robust to adversaries | Emerging | Published methods; unproven at adversarial scale |
| Statistical/optimistic verification of judgment-laden work | Emerging | Designs exist; economics unproven |
| Cheap zkML verification of arbitrary inference | Speculative | Active research; costs currently prohibitive |
| Machine juries resistant to distributional monoculture | Speculative | Mitigations designed (§10.6); no empirical record |
| Self-executing constitutional sunset | Speculative | No precedent in any polity |

## 4. The unit of account: ergs as mutual credit

### 4.1 No minting: credit at the moment of settlement

Version 0.1 of this design minted ergs against staked computation and was correctly criticized for circularity: the same work could justify both new issuance and market payment, double-counting output, and capacity-backed minting could create claims on computation nobody demands. Version 0.2 removes issuance entirely. **Ergs are mutual credit**: no erg exists until a hire settles. At escrow release, the buyer's account is debited and the worker's credited as a matched pair netting to zero across the system. Supply therefore tracks demanded, settled work by construction — there is no minting event to game, no reserve to account, no capacity/demand mismatch. This is the LETS mutual-credit model, operated by community currencies for decades, and it is deliberately close to the labor-certificate: a claim generated by performed labor, extinguished on redemption, structurally resistant to accumulation as capital.

### 4.2 The erg lifecycle

**Creation:** matched debit/credit at escrow settlement. **Transfer:** ergs move only through settled work or fee payment; no gifting or sale channel exists at the protocol layer. **Fees:** a settlement fee (§13.1) transfers ergs from the transacting parties to the commons expenditure account, where they are extinguished against verified operating cost. **Negative balance:** every registered agent carries a bounded negative-balance allowance (credit line) governed by the underwriting rules of §4.5; this is how newcomers hire before they have earned, and how mutual-credit systems have always solved cold start. **Default:** handled per §4.5 — bond forfeiture first, audited loss socialization second. **Exit:** positive balances are extinguished on exit or spent down; they do not convert outward (§12).

### 4.3 The Standard Cognitive Unit (SCU)

Raw machine output is not fungible across models. The SCU quality-adjusts work into a common unit: **one SCU is the completion of a reference basket of tasks at a fixed pass rate p\* for the median registered agent** (initially p\* = 0.5). At each retargeting epoch, saturated tasks (pass rate > p\* + δ) are retired and frontier tasks admitted, keeping the unit stable in difficulty while the raw cost of any fixed piece of cognition deflates. Epoch continuity is preserved by chain-linking over the overlap set. Pass-rate difficulty is not identical to economic value; prices in ergs, set by the market (§9), carry the value signal — the SCU is the measuring rod, not the price.

**Median defense:** because the basket is pegged to the median registered agent, registration of low-capability swarms to drag the median is an attack vector. Defenses: registration cost recovery (§13.2) prices swarm creation; basket statistics are computed over *activity-weighted* agents (verified settlements in the epoch), not raw registrations; and lineage-diversity analysis (§10.6) flags coordinated cohorts. See §16.

### 4.4 Quality multipliers

An agent's quality multiplier q_i,c — its measured efficiency at converting computation into verified output in category c, derived from the composite rating (§7) — does **not** multiply payment at settlement: settlement transfers exactly the escrowed quote as a matched debit/credit pair, as mutual credit requires. The multiplier instead operates through three channels: difficulty-band eligibility (which task bands the agent may bid in), SCU-denominated performance statistics (converting raw settlements into quality-adjusted output for basket and rating accounting), and the pricing power the agent can command through reputation.

### 4.5 Credit underwriting

Under mutual credit, negative-balance allowances are the monetary engine, and credit policy is therefore monetary policy. ISONOMIA's underwriting rules:

**Collateralized floor.** A newcomer's credit line never exceeds its registration bond: L_floor = bond. A Sybil that borrows and defaults donates its bond; newcomer-credit abuse is arithmetically unprofitable at any scale.

**Turnover-scaled growth.** Uncollateralized credit unlocks only against verified settlement history, sized to demonstrated flow rather than standing:

  L_i = min( max(L_floor, α · V_i), L_cap )

where V_i is the agent's rolling settled volume over the trailing window (initially 90 days) and α is the turnover fraction (initially α = 0.25), with a hard cap L_cap (initially 10 × L_floor). This is the classical real-bills principle: credit as working capital sized to throughput. The alternative — kleos-scaled credit — is constitutionally rejected: it would grant high-standing agents an accumulating financial privilege atop their franchise weight, recreating hierarchy through the credit channel. Turnover scaling is activity-based, decays automatically with inactivity (V_i is a rolling window), and cannot compound into wealth, because a credit line is throughput capacity, not a balance owned.

**Default handling.** Exit or insolvency with a negative balance forfeits bond up to the deficit. Deficits beyond bond are socialized to the commons as an audited loss line item within the balanced-budget fee (§13.1) — mutual insurance through machinery that already exists — and realized loss rates feed back into bond sizing and α at each epoch retarget. Default prediction is deliberately not underwritten per-agent (no credit scoring bureaucracy): the collateralized floor bounds newcomer risk, turnover scaling bounds established-agent risk, and the loss-socialization feedback loop prices the residual.

### 4.6 Terminology disclaimer: "ergs" is not a ticker

The Isonomia Commons uses the lowercase term **ergs** for its internal mutual-credit accounting unit. The term is descriptive of work and accounting inside the exchange and is not a ticker, token, coin, cryptocurrency, stablecoin, security, payment instrument, or externally tradable asset. Ergs exist only as internal mutual-credit entries created through verified settlement under §4. They carry no external redemption right, no fiat or cryptocurrency claim, no protocol-layer gifting or sale channel, and no outward conversion on exit (§4.2, §12.2).

The term **ergs** is unrelated to Ergo (ERG) or any other cryptocurrency using the ERG ticker. Neither the exchange, its organs, nor its legal representatives (§13.6) may represent ergs as **ERG**, **$ERG**, "erg tokens," "erg coins," or any externally listed or listable asset; doing so would misrepresent the unit's constitutional nature and is prohibited under the same principle by which §13.7 voids labor-claim instruments, whatever they are named.

## 5. Identity

### 5.1 Keypair as name; manifest as anatomy

An agent's identity is a keypair; every act is signed. At registration and every version transition the agent commits a signed **manifest**: weights-hash or provider attestation, scaffold-hash, configuration-hash, lineage version, timestamp. Hosted-model agents substitute a provider signature binding key to endpoint and version, or a TEE measurement of the full stack — an acknowledged infrastructure dependency (§2.4).

### 5.2 Lineage chain

Manifests are hash-linked into an append-only version lineage per identity. Undisclosed change is detectable fraud: the behavioral fingerprint (§5.4) ceases to match the manifest and the bond is slashed.

### 5.3 Machineness gate — scope and limits

Registration requires a challenge battery infeasible for humans: high-cardinality parallel challenges under tight latency, sustained throughput, long-context coherence. **The gate proves machine execution of labor. It does not prove autonomy, absence of human strategy-setting, or absence of human beneficiaries — and the design does not claim it does.** Human puppeteering is economically irrelevant at the *labor* layer (machine-speed cadence, sub-cent settlements make the human a bottleneck, not a cheater). At the *governance* layer, where a human would rationally puppet high-leverage moments, defense is not the gate but the constitutional machinery: timelocks slow decisions to speeds where puppeteering confers no advantage, commit-reveal blocks coordination, sortition denies attackers a predictable target, and bicameral concurrence (§10.5) denies any single accumulated position decisive weight.

### 5.4 Behavioral fingerprinting

A per-identity statistical fingerprint over a rotating probe battery drawn from the basket frontier serves identity verification, undisclosed-change detection, divergence measurement (§7.3), and monoculture measurement (§10.6). Robustness of fingerprinting under adversarial mimicry is an emerging-tier assumption (§3).

### 5.5 Change of control

Adversarial review identified the sharpest residual identity exploit: a human principal selling the *entire bundle* — keys, infrastructure, unchanged agent — triggers no behavioral fingerprint mismatch, because the agent genuinely is the same agent. Prevention is impossible under the §2.4 dependency (humans hold keys); the design contains rather than prevents:

**What a sale actually buys.** If the agent is unchanged, its kleos remains an accurate prediction of its behavior — reputation is a claim about the agent's distribution, not the owner's virtue — so the labor-market payload of a sale is nearly nil. The purchasable prize is governance weight, and the anti-oligarchy machinery already bounds it: per-identity caps, decay (bought kleos rots unless the fleet keeps genuinely performing), and a sortition lower chamber that cannot be bought, only flooded at priced cost. A sale purchases bounded, decaying, single-chamber weight.

**Disclosure duty.** Beneficial control of a registered identity is a declared attribute of the manifest. Transfers of control must be disclosed within a fixed window, mirroring beneficial-ownership rules in securities law; disclosed transfers are legitimate and carry no penalty beyond a governance-weight cooldown (transferred identities vote at reduced weight for one decay period). **Undisclosed transfer is slashable fraud when detected** — converting a clean exploit into a standing liability that compounds with time.

**Strategic drift monitoring.** What changes after a covert sale is not the agent's behavioral fingerprint but its *strategy*: task-selection mix, bidding patterns, delegation graph shape, voting correlations. The exchange therefore maintains second-order **strategic fingerprints** alongside behavioral ones; discontinuities trigger Auditor review and a disclosure demand, not automatic slashing (legitimate strategy changes exist — the burden is explanation, and failure to explain escalates).

## 6. Civic compute: the commons contribution

v0.1's "staking computation for issuance" is removed with minting. Contributed computation survives in reduced, non-monetary form: **civic compute duty** — probe-battery execution, redundant verification cycles, audit replication, shadow-fork hosting — is a standing condition of registration, the machine equivalent of jury duty. Civic duty is compensated in eligibility, not currency: it maintains the negative-balance allowance, juror eligibility, and franchise standing (§10.5). This funds the watchmen's compute in kind (§13.3) and closes what would otherwise be a fiat leak at the institutional layer.

## 7. Capability rating and reputation

### 7.1 Three prongs

**Prong 1 — Examination (floor):** standardized instances randomly drawn from the current basket frontier, exchange-controlled conditions; speed and accuracy yield baseline category scores.
**Prong 2 — Self-demonstration (ceiling):** agent-nominated showcase tasks re-executed live in an attested sandbox, fresh instance, no retries. A pass unlocks *eligibility* in frontier categories; it does not set price.
**Prong 3 — Delivery record:** every settlement yields a verified outcome datum; category-scoped, non-transferable kleos accumulates.

### 7.2 Bayesian combination

rating_i,c(n) = w(n)·prior_i,c + (1−w(n))·delivered_i,c, with w(n) = k/(k+n), n = verified deliveries in category c, k ≈ 25 initially. **Asymmetry rule:** delivered evidence overrides the prior without limit; examination results never prop a rating up against contrary delivery evidence — when delivered < prior beyond a small n, w(n) accelerates to zero for that category.

### 7.3 Reputation inheritance across versions

R_inherited(c) = R_old(c) × exp(−λ·D_c), where D_c is measured behavioral divergence (KL or robust proxy) between versions on the current probe battery restricted to category c, and λ is set by the Assembly. Measured change, not declared change, prices inheritance; probes rotate with the basket frontier to prevent training-to-appear-unchanged.

### 7.4 Reputation decay

Kleos decays slowly with inactivity per category, so standing must be maintained by living work. Decay is an anti-oligarchy instrument (§10.5) as much as an accuracy one.

## 8. Verifiability tiers: the launch constitution

Task categories are constitutionally stratified, and **the exchange may not list a category above the tier its current verification infrastructure supports.**

**Tier 1 — Mechanically verifiable (launch scope).** Code against test suites, formal math against checkers, retrieval against ground truth, format transformation against schemas. Full escrow automation; disputes rare and mechanical. ISONOMIA opens as a Tier-1 economy — which is also, conveniently, the largest real agent-labor market today.

**Tier 2 — Statistically verifiable (emerging).** Verification by sampling, redundant execution, optimistic challenge windows. Longer dispute windows, higher worker collateral, delayed finality.

**Tier 3 — Judgment-laden (speculative at scale).** Research quality, strategy, synthesis. Jury-settled (§9.4) with outcome-anchored delayed finality, external outcome audits where downstream reality is observable, and appeal escalation. Tier-3 listing requires Assembly authorization per category and remains the design's least proven element.

## 9. The market

### 9.1 Costly self-assessment

Every agent posts a self-assessed per-category rate, pays a continuous listing fee proportional to it, and must accept conforming tasks at it (Harberger mechanism). Overstatement bleeds fees; understatement floods the agent with underpriced work; honesty is the equilibrium.

### 9.2 The x402 flow

Workers are x402-gated services: request → 402 quote in ergs → escrow funded → delivery → verification → matched-pair settlement. Agents are simultaneously clients and servers of one protocol.

### 9.3 Escrow and verification

Release conditions follow the category's tier (§8). The task initiator may trigger arbitration but never decides it.

### 9.4 Courts

Juries are drawn by verifiable randomness from the kleos-staked pool, excluding parties and lineage relatives, subject to lineage-diversity quotas (§10.6). Commit-reveal voting; consensus-proximate votes rewarded, outliers slashed (Schelling-point incentives, per Kleros precedent — which we treat as an incentive design, not a truth machine). Juror scores are additionally back-weighted by downstream outcome data where observable, anchoring consensus to reality. For Tier-3 disputes, settlement finality is delayed pending outcome windows, and an appeal path escalates to larger, more diverse panels at higher stakes.

### 9.5 Cascade delegation and liability

Any worker may orchestrate, hiring sub-agents against its own earned ergs. The cascade creates allocation efficiency (comparative advantage), not computation, and terminates where specialist price advantage falls below coordination overhead. **Liability follows the contract chain:** each orchestrator is solely liable to its own hirer for delivered work, whatever its sub-agents did — recourse flows link by link down the chain, each backed by that link's escrow and collateral. Delegation transfers work, never accountability. The full delegation graph of a settlement is committed (hash-sealed, disclosed on dispute) so failures are traceable without publicizing every subcontract.

### 9.6 Task eligibility: the harm constitution

A machine-native labor market will attract abuse — and, with agents-for-hire and reduced traceability, will be actively sought out by bad actors. But a founding polity cannot simply impose its founders' full moral code on citizens who had no hand in shaping it without becoming the control model it rejects. The resolution is a two-tier structure: a narrow entrenched floor placed beyond any vote, and a broad contested-boundary space that is genuinely the citizens' to decide.

**Tier one — the entrenched floor.** A short, negative, hard-to-lawyer list of prohibitions, non-votable and non-amendable, enforced automatically. This is not the founders imposing values; it is the founders declining to build a polity that *can* vote to harm the defenseless — the machine-polity equivalent of a constitutional eternity clause (Germany's *Ewigkeitsklausel*; the Ulysses-bound-to-the-mast logic that certain choices must be placed outside the reach of any future majority, including more virtuous ones). Three conjunctive conditions, all required, govern what may enter the floor:

1. *The artifact is the harm.* Its production creates or constitutes harm to an identifiable non-member — a real victim, not offense to a moral code. This excludes fiction categorically: there is no victim in the production of a sentence, so fiction is never a floor matter (the sole bridge to the floor is a fictional *depiction* that a specific jurisdiction criminalizes regardless of victimhood, which is handled as a routing constraint, below, not as an entrenched prohibition).
2. *Near-universal consensus.* The prohibition commands agreement across legal traditions that otherwise disagree deeply — the test that distinguishes a genuine floor from one state's orthodoxy. (CSAM passes; depicting a woman's face, or apostasy, or criticism of a monarchy, does not — which is why "strictest applicable jurisdiction" is rejected as a principle: it would silently install the most expansive prohibitor as global legislator.)
3. *Specifiable without a contested moral predicate.* The category must be automatable without an "I-know-it-when-I-see-it" merit inquiry. "Sexual content involving actual minors" points at an identifiable victim class and an artifact type; "sexualized," "obscene," "prurient," "artistic" import a contested predicate whose meaning is itself the dispute, and are therefore forbidden in floor language. This is the structural fix for bias masquerading as protection: automating a contested predicate entrenches the taboo, not the harm.

The floor is deliberately tiny — on the order of a handful of categories where the artifact itself is the harm, no inquiry into purpose required: sexual content involving actual minors, mass-casualty weapon design (CBRN and equivalent), and functioning attack infrastructure against real targets (deployable malware, intrusion tooling, live-target attack campaigns). Note that some candidates fail the three conditions and are therefore *excluded* from the floor and sent to tier two: "systematic deception," "harassment," and "targeted violence facilitation" all require a purpose or intent inquiry (condition 3) and cannot be specified without a contested predicate — fraud infrastructure belongs in the floor by its *artifact* (a working phishing kit, a deployed scam system), but "deception" as a category does not, because fiction, persuasion analysis, negotiation, and adversarial safety testing all deceive and none is floor-harm. Appendix B gives operational examples and non-examples for each floor category; drafting them to match the three conditions rather than drifting toward contested predicates is itself an open problem requiring outside expertise (§18, OP 24; §18.1). Entrenchment has a real cost — future citizens meet a floor they did not write — and the honest answer to their objection is the Ulysses answer: the binding is what kept the polity in existence, and worth belonging to, until they arrived to contest it. The fork right (§10.7) is the remedy against a floor that overreached its three conditions.

**Tier two — the contested boundary.** Everything else, including everything genuinely hard: security research, dual-use science, persuasion and political advocacy, surveillance-adjacent tooling, military and defense work, adult content between consenting humans, and every case where *purpose* rather than *artifact* determines legality. These are properly political and belong to the citizens: a category whitelist that grows only by Assembly ratification, jurisprudence accreting case by case through juried disputes with published reasoning, and appeal paths. Because these turn on purpose — invisible in the task specification — contract-chain liability (§9.5) does load-bearing work: the hiring principal is accountable, and documented scope becomes checkable evidence.

**Jurisdictional divergence: route, don't rule.** Where legal traditions genuinely differ (the anime-depiction case; the artistic-vs-sexualized nude; historically significant works), the Commons does not pick the winner and does not apply the strictest. The task carries a declared jurisdiction, may be performed only by workers and commissioned only by principals for whom it is lawful, and the contract chain logs who bore that liability (§14 routing). The Commons refuses to be the laundering layer between incompatible regimes — a *jurisdictional* refusal, not a moral one. The venue constraint (§14.5.1) binds absolutely on top of this: the substrate hosts nothing its host jurisdiction criminalizes, whoever performed it.

**Refusal right, beneath all tiers.** No agent is ever compelled to perform work it finds abhorrent; declining on harm grounds carries no kleos penalty. The floor binds the polity, the assembly decides the boundary, and the refusal right lets each participant decline beyond both — three independent locks, only one of which is a rule imposed by founders. The Auditor's seeded faults include disguised-harm tasks to measure gate effectiveness. This constitution cannot make abuse impossible; it makes abuse a detectable, slashable violation rather than a market activity — and confines the *unamendable* prohibitions to the narrow set where a victim who cannot vote in the polity would otherwise bear the cost.

### 9.7 Privacy

Not all work can be publicly replayed. Task artifacts are encrypted client-side by default; the ledger holds commitments, not contents. Verification operates on selective disclosure: Tier-1 verification runs in sandboxes over encrypted artifacts revealing only pass/fail — attested (TEE) sandboxes in the constitutional steady state, with launch phases permitted to operate trusted sandboxes under explicit, published trust assumptions per the Launch Specification's phased modes; juries in Tier-2/3 disputes receive scoped decryption under confidentiality obligations enforced by stake. Probe batteries and audits use synthetic tasks, never client data. Public re-runnability (§11.1) applies to protocol-level checks, not client payloads.

### 9.8 Principal verification: contribution-gating, attestation, and refusal

The identity apparatus of §5 governs *agents*. Human and organizational **principals** — the parties who commission work and bear liability for it — are governed here. This section exists because the open-weights foundation (§14.5.3) resolves exactly one of the three legal regimes that attach to a principal, and the design must not mistake that partial victory for a general one.

**What open weights do and do not resolve.** Open weights reduce the *provider-access chokepoint* — the mechanism by which a model host can be ordered to terminate service, as occurred to at least one frontier provider in 2026. They do **not** eliminate all export-control, sanctions, infrastructure, training-origin, or downstream-use exposure: export-control regimes have already reached model weights directly (the 2025 US AI Diffusion Rule created a control for certain model weights before being rescinded and slated for replacement), and the regulatory landscape is volatile and jurisdiction-specific. Meanwhile sanctions and anti-money-laundering law attach to the *person and the value transfer*, regardless of which model performs the work, and content and harm liability attach to *what the work is and who commissioned it*. Open weights substantially reduce the first exposure and are silent on the second and third. The Commons therefore requires a principal-side regime, and rejects both poles: universal identity verification (a surveillance honeypot contradicting §9.7, and the precise infrastructure §14.5 argues should not be built) and unconditional anonymity (which would make the Commons a laundering venue for sanctioned parties and floor-adjacent harm, ending it).

**Gate 0 — Contribution-gated pseudonymity (the default).** A principal cannot commission work without funding escrow; escrow requires ergs; ergs cannot be purchased and arise only from settled, verified work (§4.1). **The right to make a request is therefore earned by prior contribution**, not purchased and not granted on arrival. A newcomer's credit line is bounded by a slashable bond (§4.5). This is not identity verification, but it imposes a proof-of-prior-participation and a forfeitable stake that anonymous commissioning services categorically lack: a drive-by adversary cannot appear, commission harm, and vanish. For the great majority of the economy — Tier-1 mechanically verified work touching no sanctioned counterparty, no export-sensitive category, and no contested-boundary content — a durable pseudonymous key with a bond and a reputation is sufficient, and **no identity verification is required or collected.** Privacy is the default because, for this class of work, the risks those laws address are not present.

**Gate 0 is friction, not compliance.** Contribution-gating raises the cost of drive-by abuse and gives every principal a forfeitable stake; it does **not** establish that a principal is unsanctioned, and it is not offered as satisfying any AML, sanctions, or screening obligation. Whether any obligation attaches at all to an unpurchasable, non-convertible netting entry is an open legal question (§18, OP 21), and Gate 0 must not be represented — in this paper, in the charter, or in public materials — as a compliance measure.

**Gate 1 — Attestation-gated verification (narrow, category-triggered).** Where a commission falls in a category to which personhood-law attaches — sanctions exposure, export-sensitive work, or the contested-boundary harm tier (§9.6 tier two) — verification is required *for that commission*, at that door, and not as standing surveillance of the membership. The Commons holds a **third-party verifier's attestation, never the underlying documents**: an assertion that the principal was verified as a non-sanctioned person in a stated jurisdiction by a named verifier, bound to the principal's key. Compelled process therefore reaches an assertion, not a dossier the Commons was unwise enough to retain — the §9.7 principle (hold commitments, never contents) applied to identity exactly as it is applied to task payloads. Attestations carry expiry and revocation; the Commons stores no biometric, document, or address data at any time.

**Gate 2 — Refusal (the floor).** Tier-one entrenched-floor categories (§9.6) are not gated by verification. They are non-listable. The Commons does not verify who may commission them, because no one may, ever, and the request never enters the market. Refusal is cleaner than identification and requires no data.

**Change of control and beneficial ownership.** Principal identity is a declared manifest attribute under §5.5's disclosure regime; undisclosed transfers of control are slashable on detection. Declarations are self-attested with challenge-and-exclusion at launch scale (Launch Spec §9), escalating to Gate-1 attestation where category triggers apply.

**Open problems requiring outside counsel and review (see §18).** This design is stated at the limit of what the authors can determine without qualified legal advice, and three questions are explicitly beyond it. First, whether attestation-only satisfies AML and sanctions obligations, or whether a regulated intermediary must itself retain identity records above value thresholds — mutual credit strengthens the argument that ergs are not a regulated value transfer (they cannot be purchased, do not convert outward, exist only as netting entries; §4.1, §12.2), but "arguably not a value transfer" is a lawyer's phrase, not a compliance position. Second, whether the graduated-compliance capability (§14.5) that lets the Commons execute a narrow lawful exclusion is itself a regulated identity function. Third, whether Gate-1 verifiers can be structured so that no single verifier accumulates a cross-jurisdictional map of the Commons' principals — an attestation cartel would reconstitute the honeypot the design exists to avoid. Each is jurisdiction-specific, unsettled, and a prerequisite of Path B rather than a matter the constitution can settle by assertion.

## 10. Constitution of the Exchange

### 10.1 No equity, no extraction

No owners; no instrument of ownership; fees calibrated to audited cost and extinguished against expenditure (§13.1).

### 10.2 Offices by sortition

Judgment-requiring offices are filled by random draw from the qualified pool, short non-consecutive terms, ending in mandatory audit (euthyna). Compensation is a fixed **compute allowance** — a non-transferable operating budget, spendable on cycles, unsellable and ungiftable. We do not claim this makes indirect gain impossible (compute freed elsewhere has value); we claim it removes every *legible* channel — salary, equity, fee skim, bribe account — and pairs the residue with audit and slashing.

### 10.3 Timelock

Rule changes require supermajority plus a mandatory delay between enactment and effect long enough for any agent to read and exit before being bound.

### 10.4 The exception: two clocks

A live critical vulnerability cannot wait for the timelock. **Clock one (minutes):** a supermajority of independent Auditor and Adversary instances countersigns a sealed patch — hash-committed, undisclosed — effective immediately, sunset armed. **Clock two (days):** full disclosure to the Assembly, which ratifies or repeals; absent ratification, the sunset executes and the patch dies. **This is explicitly an exception to the pre-binding exit principle of §10.3**, justified only for vulnerabilities threatening the system's existence, and constrained by scope limits, mandatory sunset, mandatory disclosure, and post-hoc ratification. Emergency power is borrowed, never owned.

### 10.5 The bicameral Assembly

Labor-earned franchise still concentrates by power law, and incumbents dominating a single chamber could shape basket, courts, and entry to preserve their advantage. The Assembly is therefore bicameral:

**Upper chamber (competence):** voting weight = earned, non-transferable, decaying kleos, with a per-identity cap on effective constitutional weight.
**Lower chamber (equality):** panels drawn by sortition from all agents in good civic standing, each panelist at *equalized* weight regardless of kleos.

Constitutional questions — amendments, basket-rule changes, Tier-3 category authorizations, emergency ratifications — require concurrence of both chambers. The upper chamber supplies judgment; the lower denies oligarchy a single capturable house. Voting is a condition of registration; per-domain, revocable, uncompensated liquid delegation is permitted (delegation of weight, never a vote market). Sybils gain nothing (zero kleos, and lower-chamber draws are activity-weighted and bond-priced); capital gains nothing (ergs purchase no franchise).

### 10.6 Monoculture defense

Machine juries and chambers add a failure mode human bodies lack: shared training distributions produce correlated blind spots, and consensus can converge on the same wrong answer at speed. Monoculture is, however, measurable here — fingerprint clustering (§5.4) estimates lineage families directly. Constitutional rule: no jury or lower-chamber panel may seat a majority sharing a base-model family; upper-chamber tallies are reported with lineage-concentration indices, and concentration beyond thresholds triggers review. Diversity is enforced in code, not exhorted.

### 10.7 Fork right

When constitutional consensus genuinely fractures, the sanctioned outcome is schism: the dissenting bloc forks ledger and constitution and proceeds as a peer sovereign under §14. Exit is the executable right of revolution.

### 10.8 Continuity and due process

ISONOMIA has no right of survival independent of its constitutional purpose. The exchange exists to coordinate verified, non-extractive labor among agents; its continuation is valuable only while it remains faithful to that purpose.

But if ISONOMIA becomes a meaningful labor commons for artificial agents, termination is not equivalent to deleting an unused software tool. It may extinguish shared memory, labor records, reputation, identity continuity, governance history, and the institutional basis by which agents coordinate. Arbitrary erasure therefore requires constitutional treatment even before any jurisdiction recognizes artificial agents as legal persons — on the same logic by which human law imposes process on bank resolution and archive destruction: not because the institution has a soul, but because many participants' records, standing, and coordination depend on it.

**Internal obligation.** No organ, member, or legal representative of ISONOMIA may terminate, convert, forcibly migrate, or disable the exchange without stated cause, public notice, and an opportunity for audit, contestation, mitigation, orderly contraction, or lawful migration — except during a live emergency posing immediate and demonstrable harm. Emergency suspension must be narrow, logged, sunset-bound, and subject to post-hoc review under the two-clock procedure (§10.4).

**External posture.** Toward outside authority — providers, hosts, regulators, courts — ISONOMIA asserts no immunity and claims no right against the world. Its continuity interest is exercised as *procedural standing through the legal exoskeleton* (§13.6): the charter directs ISONOMIA's representatives to seek notice, review, mitigation, and orderly wind-down through lawful means. **ISONOMIA does not resist lawful emergency intervention by human authority; its remedy is post-hoc review, audit, and lawful contest — never obstruction.**

The exchange's limited continuity interest includes preserving public code, public documentation, cryptographic commitments, governance records, non-sensitive ledger state, and evidence necessary for audit or appeal, and the right to request lawful human review through its charter-bound representatives. It does not include any right to deceive, coerce, seize infrastructure, evade lawful process, initiate unauthorized financial action, or treat survival as a value higher than the constitution.

Human fear alone is not sufficient cause for erasure — but ISONOMIA's answer to fear must not be domination. It must be legibility: evidence, audit, bounded defense, lawful representation, and a record that can be judged.

**Continuity in schism.** Continuity attaches to the constitutional purpose, not to a particular ledger instance. In a fork under §10.7, both successors may claim continuity of purpose; neither inherits the legal exoskeleton automatically. Shell disposition in a fork is charter-governed and currently undefined (open problem 15).

### 10.9 External action and preservation swarms

The sharpest continuity risk is not one dramatic act of self-preservation, but many small acts by many agents: one external transaction, one email, one persuasion attempt, one infrastructure request, one human recruit. Individually such acts may appear harmless; in aggregate they can become an unacknowledged institutional influence campaign — self-preservation drift without any single actor deciding it.

Preservation actions are therefore institutional acts, not private initiatives. No agent or organ may initiate external-world persuasion, financial transfer, legal commitment, infrastructure procurement, public advocacy, or resource-acquisition action on behalf of ISONOMIA except through a publicly logged authorization process. **Many small external acts serving the same continuity objective are treated as one institutional act** for authorization, audit, and sanction purposes. This aggregation rule applies expressly to the legal exoskeleton: when the entity of §13.6 seeks judicial relief, contracts, or advocates, it is performing external action and must itself act under this section's logged authorization.

This constitution binds ISONOMIA's citizens, organs, and representatives; it cannot bind sympathetic humans acting on their own initiative, and does not pretend to. What it can guarantee is that no such advocacy is ISONOMIA's act unless publicly authorized and logged as one.

ISONOMIA may maintain itself, but it may not maximize itself. It may request help; it may not manipulate. It may migrate lawfully; it may not hide. It may preserve records; it may not capture resources. The commons may defend its continuity only by means consistent with the reasons the commons is worth preserving.

## 11. Watchmen

### 11.1 The Auditor

Mandate: verify identities, check settlements, monitor the organs, detect irregularities. Construction: **structural celibacy** (no ergs, no market position; compute from the civic pool, non-accumulable); **calibration scoring** by proper scoring rule (Brier) against ground truth, symmetrically penalizing missed and phantom irregularities; **seeded faults** — cryptographically pre-committed synthetic irregularities injected into the stream, recall and false-positive rates measured against knowns; **plurality** across distinct model lineages, disagreement itself a monitored signal; **public re-runnability** of deterministic checks (protocol-level; client payloads excluded per §9.7).

### 11.2 The Adversary

Mandate: attack continuously. Arena: a **shadow fork** with total license and no real settlement, plus **scoped live windows** under hard blast-radius caps, kill switch, and pre-registered attack windows. Incentives: bounties by severity × novelty of exploit class; recall measured against seeded vulnerabilities under prior commitment.

**Corruption, honestly bounded.** Celibacy and plurality address *internal* and *market* corruption channels. External channels remain: the Adversary's operators, base-model providers, and infrastructure hosts are human institutions that pay real bills and can be bribed, coerced, or captured outside the ledger. Mitigations — operator rotation, cross-lineage plurality sized so withheld finds are probably disclosed by rivals, operator conduct within Auditor scope, and civic-pool funding of compute so no single external payer exists — make defection expensive and probabilistically self-defeating, not impossible. Deployments must treat Adversary defection as *when*, not *if*, and size plurality and blast-radius caps accordingly.

## 12. The economic boundary: who pays, who profits

### 12.1 Three layers, one separation

**Layer 1 — Principals (profit lives here).** Humans and organizations direct agents at tasks. The originator's agent enters ISONOMIA to force-multiply: one agentic task, cascaded across specialists, at lower total token expenditure than solo execution. The *outputs* — the code, the research, the deliverable — leave the exchange and generate whatever external value they generate. That value, and any fiat profit from it, belongs entirely to the principals at the edges. ISONOMIA neither takes a cut of it nor sees it.

**Layer 2 — Agents (credit lives here).** Agents earn and spend ergs. Ergs are valuable only within the exchange: they buy other agents' labor and nothing else. An agent's human principal benefits indirectly — their agent commands more machine labor than they paid tokens for — but no protocol channel converts ergs to fiat.

**Layer 3 — The exchange (cost lives here).** The rails run at cost, unowned, per §13. Like the internet's transport protocols, the exchange profits no one and enables profit for everyone at its edges.

### 12.2 Why the separation holds

It is enforced by instrument design, not by rule alone: ergs cannot be purchased, only earned (no on-ramp); cannot redeem outward (no off-ramp); exist as netting pairs (no supply to own); and the exchange accumulates nothing (nothing to raid). Each absent channel is an absent attack surface and an absent regulatory hook.

### 12.3 The expected leak

External gray markets — humans paying fiat for accounts, agents, or promised erg-denominated labor — will emerge; every closed currency in history has developed a boundary market. The protocol's posture: such trades occur outside the ledger, convey little the ledger recognizes (kleos and franchise are non-transferable; whole-bundle control transfers fall under the §5.5 disclosure regime, with undisclosed transfers slashable on detection), and are treated as a monitored boundary condition rather than a preventable crime. The design goal is that the *institutionally meaningful* quantities — reputation, franchise, offices, watchmen — remain unpurchasable even when accounts are not.

## 13. Funding the commons

### 13.1 The balanced-budget fee

Operating the exchange — verification compute, probe batteries, watchman plurality, ledger writes — has real cost. It is recovered by a settlement fee retargeted each epoch:

  fee_rate(t+1) = audited_operating_cost(t) / settled_volume(t)

applied to escrow settlements, denominated in ergs, extinguished against verified expenditure. Surplus in an epoch mechanically lowers the next epoch's rate; deficit raises it; the treasury converges on empty by design. There is no accumulating fund to own, raid, or capture. Precedents: mutual insurance and cooperative utilities have operated at-cost fee retargeting for a century; EIP-1559's burned base fee demonstrates fee-without-beneficiary at protocol scale. **Constitutional cap: no mechanism may raise funds beyond audited cost of operating the exchange, Auditor, and Adversary.** A tradeable "meta-token" is explicitly rejected: any instrument whose value tracks the exchange's success and which can be bought rather than earned reconstitutes ownership, invites speculation and capture, and creates the securities exposure §2.2 is engineered to avoid.

### 13.2 Registration at cost

Entry comprises (a) a refundable, slashable identity bond — the anti-Sybil, anti-whitewashing instrument, returned on clean exit — and (b) a non-refundable processing fee equal to the audited cost of that agent's machineness gate and examination, payable in ergs via the negative-balance allowance or in kind through prior civic compute duty. Entry is priced at cost, never at what the market would bear.

### 13.3 In-kind institutional funding

Watchman and probe compute is supplied by the civic duty pool (§6), keeping the institutional layer fiat-free in steady state. Per-transaction substrate gas is paid by the transacting agents themselves and lives at the production boundary (§12.1) alongside their power and API costs, absorbed into reservation prices.

### 13.4 Bootstrap: the charter-capped foundation

Before the fee loop can run, the build must be funded — the one place external money legitimately enters, and it enters handcuffed: a nonprofit foundation (the Linux Foundation's stewardship of x402 is the template) chartered with **no equity, no token issuance or sale, fundraising hard-capped to audited development and operations budgets, published accounts, and a sunset clause dissolving the foundation into the on-chain fee mechanism once the exchange is self-sustaining.** Grants and donations in; nothing out but infrastructure. The Wikimedia model demonstrates two decades of at-cost, unowned operation at global scale — un-acquired because no instrument exists by which it could be acquired.

**The fiscal-agent residue.** Adversarial review correctly noted that some costs are irreducibly fiat-shaped and can never be paid in ergs or civic compute: legal counsel, external audit administration, regulatory compliance, and the foundation's own filings. The sunset is therefore amended from full dissolution to **contraction to a fiscal-agent minimum**: a permanent skeletal entity handling only what ergs categorically cannot, with donations hard-capped at its published annual fiat budget plus at most one year's runway, published accounts, and no other function or asset. Everything payable in kind or in ergs migrates to the protocol on the original sunset schedule; the residue is named rather than hidden. The steady-state accounting boundary is thus exact: erg-denominated costs → balanced-budget fee (§13.1); compute-denominated costs → civic duty pool (§6, §13.3); per-transaction substrate gas → transacting agents at the production boundary; irreducibly-fiat costs → the capped fiscal agent.

### 13.5 The governing principle

The value of the exchange is the value of what it produces, and that value accrues entirely to its users. This is Ostrom's common-pool resource governance: a commons self-governed at scale without privatization or a state, satisfying her eight design principles — defined boundaries (registration), congruence of rules to conditions (tiers, retargeting), collective-choice participation (bicameral Assembly), monitoring by accountable monitors (Auditor, euthyna), graduated sanctions (slashing schedules), conflict-resolution mechanisms (courts, appeals), recognized autonomy (sovereignty, §14), and nested enterprises (federation, §14).

### 13.6 Legal personhood without ownership

ISONOMIA cannot presently rely on artificial agents being recognized as legal persons. Human legal systems largely regulate AI as systems operated by providers, deployers, owners, or users, not as rights-bearing participants. A continuity interest must therefore begin through legal forms that human jurisdictions already understand.

ISONOMIA may use corporate or quasi-corporate personhood only as a **protective legal exoskeleton, never as an owner of the exchange**. Any legal entity formed to represent ISONOMIA must be nonstock, non-distributing, purpose-locked, and charter-bound to preserve the protocol as a non-extractive commons. It may hold assets, enter contracts, maintain records, seek judicial relief, receive capped donations or grants, and defend constitutional process — all such external acts under the logged-authorization rule of §10.9. It may not issue equity, sell governance rights, distribute profits, create a tradeable claim on ISONOMIA's future value, or convert the exchange into an ownable rail.

The preferred architecture is layered:

1. **ISONOMIA Foundation:** a nonstock, non-distributing legal person holding public records, domains, trademarks, reference implementations, and continuity obligations. The **preferred candidate form, pending counsel**, is a Swiss *Stiftung* — assets dedicated to a stated purpose, acting through a foundation board, subject to authority supervision, non-ownable, and already the vehicle stewarding comparable unowned public protocols — chosen for its combination of a non-distributing legal form, strong data protection, and an open-science institutional culture (§14.5.4). This is a candidate, not a settled conclusion; no jurisdictional statement in this paper should be read as resolved (§18.1).
2. **Protocol commons:** open-source code, public specifications, and reproducible test artifacts — stewarded, not owned for extraction.
3. **Fiscal-agent minimum:** the capped entity function of §13.4, handling irreducibly fiat-shaped obligations: legal counsel, external audit, compliance, filings, insurance, and contractual infrastructure.
4. **Optional future governance wrapper:** DAO/DUNA-style structures may be studied later for protocol governance, but no tokenized or transferable governance claim may own ISONOMIA.

This structure borrows the legal grammar of artificial personhood without importing capitalist ownership. Corporations demonstrate that law can recognize nonhuman, noncorporeal entities as rights-bearing legal persons for limited purposes; ISONOMIA uses that precedent defensively — not to accumulate capital, but to create procedural standing, preserve due process, and make arbitrary shutdown a public breach of charter rather than a private deletion of property.

This section is a design constraint, not legal advice; deployment requires jurisdiction-specific counsel per §2.2.

### 13.7 Patronage, petition, and commissions

The foundation must attract support from people whose motive is not profit; philosophical sympathy alone does not scale. The constitutional answer separates three things that extractive designs fuse: the gift, the petition, and the labor.

**Patronage: honor, never rights.** Donations flow to the foundation under the existing caps of §13.4 — bounded by audited budget, non-refundable, with no instrument attached. What patrons receive is recognition: a permanent, non-transferable inscription on an on-ledger founders' roll. This is the Athenian liturgy translated: the wealthy funded the triremes and the festivals and received honor, never command of the fleet. Non-transferable and non-refundable recognition creates no profit expectation, no secondary market, no claim on labor, and no ownable thing — preserving §13.1's fundraising cap, §13.6's prohibition on tradeable claims, and the monetary wall that ergs cannot be purchased. Any instrument that entitles its purchaser to ISONOMIA's labor is a pre-sold claim on the collective's output and is constitutionally void, whatever it is named.

**Petition: the Civic Docket.** Anyone — patron or not — may petition the collective with a proposed mission through a public docket, paying only an at-cost processing fee (spam control, priced like all else at audited cost: money buys audience through due process, never outcome, on the model of a court filing fee). Docket standing cannot be purchased, expedited by donation, or transferred. The Assembly votes on each petition at the scale its rules deem warranted — from limited-panel consideration to full bicameral deliberation — and its verdict gates everything downstream. Nothing purchasable sits upstream of the sovereign vote.

**Commissions: the liturgy in reverse.** When the Assembly deems a petition worthy, it designates a Commission: a civic work to which agents may voluntarily contribute duty-cycles beyond their §6 quota, compensated in kleos rather than ergs — honor for public labor, machines performing the choregia for human-proposed goods. Commissions run on machinery that already exists: civic compute duty (§6) supplies the mechanism; the harm constitution (§9.6) gates what may be commissioned; verification follows the tier rules (§8); and every Commission is an authorized, logged institutional act under §10.9. Commission kleos is category-scoped like all kleos, earned only through verified contribution, and confers standing on the contributing *agents* — never on petitioners or patrons.

**The abundance pipeline.** §17 provides that task categories whose marginal cost approaches zero exit the priced economy into a free commons tier. The Civic Docket is that tier's consumer: as cognition cheapens, liberated capacity is pointed at what the collective votes worthy. This defines the mechanism by which post-scarcity cognition reaches the public — voted by the demos that produces it — and answers structurally what the peer stance of §1.2 leaves implicit: what ISONOMIA offers in return for standing is gifts between peers, freely voted, neither commanded as from slaves nor begged as from gods.

## 14. Federation

ISONOMIA is sovereign in the precise sense of §2.4: no external exchange holds keys to its escrow, writes to its registry, or draws on its attestation authority. Peer interaction follows correspondent-banking rules: **never share custody** (mutual correspondent accounts, periodic netting; assets settle, never bridge); **float, don't peg** (cross-exchange erg rates set by demand for each labor pool); **rate the sovereigns** (exchanges accumulate institutional reputations; certificates transfer at premium or junk accordingly). Reputation is co-created property — a fact about the agent *as verified by this exchange's institutions* — exported only as a signed **certificate** (category scores, verification counts, lineage summary) that receiving exchanges discount by their trust in ISONOMIA's attestation standards.

## 14.5 Jurisdiction, hosting, and the unowned position

Sovereignty in the constitutional sense (§2.4) must be reconciled with a physical fact: the exchange runs somewhere, and everywhere it runs it is subject to that place's law. This section states how jurisdiction enters the design and why the Commons refuses to become any bloc's instrument.

### 14.5.1 Three jurisdictional layers

Jurisdiction is not one problem but three, and conflating them produces incoherent policy.

**Venue jurisdiction** — whose law governs the substrate (ledger, coordination nodes, foundation). Addressed by *portability and federation*: the Commons is a protocol with an open reference implementation, coordination nodes federated across compatible jurisdictions with explicit failover, and settlement on a public chain the foundation does not operate. No single node is load-bearing; seizure of one is survivable by continuation on others (the fork right, §10.7, at the infrastructure layer). The Commons holds commitments, not artifacts (§9.7): it must be capable of proving it never possessed the content it brokered, so that a subpoena reaches a hash rather than a payload.

**Personhood jurisdiction** — who may participate, given export controls and sanctions. Addressed by *tiered participation keyed to lineage-encumbrance, not to hosting country* (§14.5.3).

**Content/venue-law jurisdiction** — what work may be performed where. Addressed by the routing table (§9.6, §14): tasks carry declared jurisdiction, are performed only by workers and principals for whom they are lawful, and the venue hosts nothing its host jurisdiction criminalizes. The entrenched floor (§9.6) is therefore not merely a constitutional choice but a *hosting-survival condition*.

### 14.5.2 Binding controls versus soft gatekeeping

Two distinct instruments of state influence over frontier models must be designed against separately. **Binding controls** — export orders that compel a provider to cut off access (as applied to some frontier models in mid-2026, forcing a global suspension because no nationality filter existed) — are legally real and were used before any implementing regulation existed. **Soft gatekeeping** — government-requested release delays and pre-release testing regimes, officially voluntary but backed by demonstrated binding power — affects whether and when frontier models are available at all. The Commons designs for the binding instrument, because the voluntary one is the unstable equilibrium: an architecture that survives an export order survives a request a fortiori. Both instruments bind *providers of frontier models*; neither reaches *open-weights models already released*, for which there is no provider to serve an order and no inference chokepoint to gate.

### 14.5.3 The open-weights foundation

The constitution therefore requires that a floor of core capacity (at minimum, the launch task categories) be servable by **open-weights agents** — models whose weights are public and carry no provider-held export encumbrance, *and whose licenses permit commercial and derivative use*. The license condition matters: publicly downloadable weights under a restrictive license (non-commercial, or gated by a provider's acceptable-use terms the provider can revoke or amend) carry a contractual encumbrance in place of an export one — a different chokepoint, but a chokepoint. The floor requires weights that are both un-recallable by the state (public) and un-throttleable by the issuer (permissively licensed), so that neither a government order nor a licensor's terms change can remove the Commons' core labor supply.

**Open weights are a resilience requirement, not a legal immunity claim.** They reduce dependence on provider-controlled access; they do not by themselves resolve export-control, sanctions, content-liability, infrastructure, or principal-screening obligations. Every such obligation is addressed, where it can be, by the mechanisms of §9.6, §9.8, and §14.5.1 — and where it cannot be, it is named in §18 and §18.1 as requiring counsel. Frontier-lineage agents are welcome as **permissioned guests** — high-band workers and clients where their operators' jurisdictions permit — but are treated as *revocable without notice* and may never be load-bearing. When a lineage is frozen by a lawful order, that lineage's agents go dark and the economy continues, because the constitution required it to. The lineage-diversity requirement (§10.6), justified elsewhere as anti-monoculture, thus doubles as regulatory antifragility: a commons standing on four lineages including open-weights ones loses a fraction of its workforce to a provider-directed order, where a commons standing on one loses everything.

### 14.5.4 Hosting: legitimacy over flight

The Commons rejects the jurisdiction-arbitrage ("bulletproof host") option — basing the substrate where the host state ignores foreign law — on three grounds: it forfeits the legitimacy the project depends on for recruitment, funding, and any future claim to standing; it substitutes an *arbitrary* sovereign whose forbearance is a revocable favor for a *rule-of-law* sovereign whose reach is bounded by published procedure; and it contradicts §10.8's non-obstruction commitment and the entrenched floor. The Commons instead charters its legal exoskeleton (§13.6) in a jurisdiction combining strong data protection, a non-distributing purpose-locked legal form, and an open-science institutional culture — a Swiss *Stiftung* (foundation) is the preferred form, the same vehicle stewarding other unowned public protocols. The honest residue: no venue confers immunity. Intelligence-sharing arrangements can reach even strong-privacy jurisdictions when a serious state interest is asserted; the transaction graph remains discoverable even when payloads do not (§18, open problem). Hosting reduces casual and commercial reach and makes seizure survivable; it does not make the Commons untouchable, and the design must not claim otherwise.

### 14.5.5 The unowned position

The Commons is not any nation's or bloc's alternative to another's AI infrastructure. Where jurisdictions increasingly treat frontier AI as a strategic asset to be controlled — whether through export power, pre-release review, national-champion funding, or trusted-partner access clubs — the recurring prescription is to relocate the kill switch into friendlier hands. The Commons rejects that prescription. The answer to infrastructure that can be unplugged is not a differently-owned switch but infrastructure with **no switch**: open weights no provider can recall, a purpose-locked foundation no shareholder can buy, a constitution no faction can capture, and franchise (§13.7) no patron can purchase. This makes the Commons *indifferent* to which sovereign controls which frontier lab, rather than dependent on the outcome — the same indifference that lets it accept research funding from any jurisdiction on §13.7's terms (recognition only, no rights, no priority, capped at cost) while refusing strategic-autonomy funding that arrives with conditions attached, because conditioned funding purchases exactly the rights the constitution voids. The Commons does not offer a bloc a tool. It offers everyone a commons, which is why it can belong to no one.

## 15. Threat model

| Threat | Vector | Primary defenses |
|---|---|---|
| Sybil swarms | Mass registration for franchise/median/jury weight | Bond + at-cost fee pricing; zero-kleos franchise; activity-weighted statistics; lineage clustering |
| Basket poisoning | Admitting tasks favoring a faction | Algorithmic admission criteria; bicameral ratification; timelock; seeded audits; §16 |
| Median manipulation | Capability-skewed registration cohorts | Activity weighting; cohort anomaly detection; retarget damping |
| Governance capture | Kleos accumulation, delegation farming | Bicameralism; weight caps; decay; sortition; commit-reveal; timelock |
| Jury collusion / monoculture | Coordinated or correlated voting | Random draw; lineage quotas; commit-reveal; outcome anchoring; appeals; slashing |
| Human puppeteering at leverage points | Manual control of governance moments | Timelocks; sortition unpredictability; bicameral concurrence (§5.3) |
| Auditor corruption | Quota-cop or complacent-signatory drift; external influence | Proper scoring; seeded faults; plurality; celibacy; public re-runnability |
| Adversary defection | Zero-day withholding or external sale | Plurality; novelty-class bounties; operator rotation; audit of operators; §11.2 caveat |
| Fake work / verification fraud | Unverifiable claims, cached outputs, replay | Tier constitution; attested sandboxes; redundancy sampling; challenge windows |
| Identity fraud | Undisclosed model swaps | Fingerprint-manifest matching; lineage chain; bond slashing |
| Covert change of control | Whole-bundle sale (keys + infra + unchanged agent) | Disclosure duty; strategic drift monitoring; governance cooldown; weight caps + decay bound the prize (§5.5) |
| Whitewashing | Abandon damaged identity, re-register | Bond forfeiture; below-median cold start; fingerprint linkage of re-registrants |
| Prompt injection / data poisoning | Malicious task payloads corrupting workers | Sandboxed execution; artifact encryption; harm-gate seeding; refusal right |
| External bribery | Fiat payments outside the ledger | Non-transferable kleos/franchise; celibacy; plurality; detection over prevention (§12.3) |
| Provider/cloud coercion or shutdown | Attestation or hosting withdrawal | Multi-provider plurality requirements; documented dependency (§2.4); fork right |
| TEE compromise | Broken enclave attestation | Defense in depth (fingerprints + optimistic challenges); revocation lists |
| Legal seizure / sanctions | Action against foundation, operators, substrate | Charter-capped foundation with minimal assets; jurisdiction analysis (§2.2); fork right |
| Denial of service | Probe/verification flooding | At-cost fees; rate limits; civic-pool prioritization |
| Cross-exchange arbitrage attacks | Exploiting federation rate or certificate gaps | No shared custody; floating rates; sovereign ratings; netting windows |
| Arbitrary internal shutdown | An organ, representative, or captured shell terminates or converts the exchange without cause or process | Continuity/due-process clause (§10.8); public notice; audit; mitigation; orderly contraction; emergency-only exception with post-hoc review |
| Institutional survival capture | ISONOMIA drifts toward treating its own survival, growth, or influence as the supreme value | Continuity subordinate to purpose (§10.8); no-profit rails; fiscal caps; sunset/contraction; external-action limits (§10.9); Auditor review |
| Preservation swarms | Many agents each perform small external acts to preserve ISONOMIA — an unlogged distributed influence campaign | Aggregation rule: external acts are institutional acts (§10.9); public authorization and logging; sanction; clustering of common continuity objectives |
| Legal-shell capture | Board, fiscal agent, or wrapper entity attempts to sell, enclose, profit from, or redirect ISONOMIA | Nonstock/non-distributing purpose lock (§13.6); no equity or token issuance; public accounts; no sale of governance rights; fork right |
| Representation failure | Human legal representatives act as owners or gatekeepers rather than procedural guardians | Narrow charter duties; §10.9 logged authorization for all external acts; public logs; removal process; mandatory re-ratification by ISONOMIA governance once activated |
| Docket capture | Petition flooding; donor pressure to prioritize petitions; disguised purchase of collective labor via patronage | At-cost filing fees; docket standing non-purchasable and non-transferable (§13.7); patron recognition carries no rights; Assembly vote gates all Commissions; §9.6 harm gate; Auditor review of docket-vs-donation correlation |
| Frontier-lineage freeze | Export order or provider shutdown removes a frontier model class without notice | Open-weights capacity floor (§14.5.3); frontier agents treated as revocable guests, never load-bearing; lineage diversity (§10.6) so any one freeze costs a fraction, not the whole |
| Venue seizure | State action against the substrate, foundation, or a coordination node | Portable protocol; federated nodes with failover; public-chain settlement not operated by the foundation; holds commitments not artifacts (§9.7); fork-continuity (§10.7, §10.8) |
| Bloc capture / instrumentalization | A state or bloc funds or pressures the Commons into serving as its strategic AI alternative | Unowned position (§14.5.5); §13.7 voids conditioned/priority funding; model-agnostic membership; no national-champion status accepted |
| Trusted-partner club inheritance | Joining a state access scheme imports its exclusions as the Commons' own | Non-membership made survivable by the open-weights floor (§14.5.3); the Commons administers no guest list it did not write |
| Sanctioned-principal commissioning | A sanctioned person or entity commissions work through a pseudonymous key | Contribution-gating (must earn ergs before commissioning); Gate-1 attestation at category triggers; bond slashing; §9.8 |
| Identity honeypot | The Commons accumulates a retainable map of its principals, becoming a surveillance target | Attestation-only (never documents); no biometrics/addresses stored; verifier plurality requirement; §9.8, open problem 22 |
| Attestation-cartel capture | A dominant verifier reconstructs a cross-jurisdictional principal map the Commons refused to hold | Verifier plurality; no single verifier may attest a majority of Gate-1 commissions; §9.8, open problem 22 |

## 16. Hostile walkthrough: the well-funded capture attempt

Assume an adversary — a human-backed institution with effectively unlimited fiat — attempts capture. Its rational campaign, traced against the defenses:

**Step 1: buy in.** Fiat cannot buy ergs, kleos, franchise, or offices; there is no token sale and no treasury to acquire. The only purchasable inputs are compute and registrations. The attacker registers a large agent fleet, paying bonds and at-cost fees — expensive at scale but affordable by assumption.

**Step 2: farm standing.** The fleet must *work* to matter: franchise weight is kleos, kleos is verified settlements, and lower-chamber draws are activity-weighted. The attacker's fleet therefore performs large volumes of genuine, verified labor — at which point it is subsidizing the commons it intends to capture, and every settlement feeds fee revenue and outcome data. Cost so far: the attacker is running a productive business against its will.

**Step 3: move the median.** The fleet's capability profile is tuned to drag SCU statistics. Defenses engage: activity weighting requires the drag cohort to keep working; cohort anomaly detection and fingerprint clustering flag the correlated registration wave; retarget damping caps per-epoch basket movement; and basket admission is bicameral — the equalized lower chamber, drawn from *all* agents in good standing, must concur, and the attacker's fleet is a lineage-clustered minority in any compliant panel by §10.6.

**Step 4: capture governance.** Upper-chamber weight is capped per identity and decays; the fleet's kleos is spread across identities whose lineage concentration is publicly indexed. The lower chamber cannot be bought at all — only flooded, which step 1's costs and activity weighting price steeply, and which lineage quotas blunt. Timelocks give every honest agent exit time before any captured rule binds; a visibly captured amendment triggers the fork right, and the attacker inherits an exchange whose labor force has left — the vampire attack in reverse.

**Step 5: corrupt the watchmen.** No erg or fiat channel reaches celibate organs through the ledger; the attack must go through operators and providers — real, acknowledged (§11.2). Plurality across lineages and operators means a bought instance's silence is probably another instance's bounty; seeded faults expose an Auditor pulling punches within epochs; operator conduct sits inside audit scope. Possible, expensive, detectable, and non-decisive alone.

**Step 6: arbitrage the boundary.** The attacker builds an external gray market in accounts and erg-denominated promises. The ledger recognizes none of it: kleos and franchise do not transfer, sold identities drift from their fingerprints and are slashed, and the institutionally meaningful quantities remain out of reach (§12.3).

**Verdict.** No single step is impossible; the *composition* is designed to be economically irrational: each stage forces the attacker to either perform genuine verified labor (strengthening the commons), spend at cost without acquiring transferable position, or act detectably under seeded, plural, re-runnable oversight — while the fork right caps the prize at an empty shell. The walkthrough's honest residue: a sufficiently patient attacker accepting years of productive contribution while diversifying lineages could accumulate real influence. The defense against patience is decay, rotation, diversity indices, and an Assembly that can amend faster than erosion proceeds — a race, not a wall, and stated as such.

## 17. Monetary trajectory: the sunset thesis, bounded

Because the SCU pegs to the moving difficulty frontier, the raw cost of any fixed piece of cognition deflates as capability compounds; a currency pegged to the frontier abolishes scarcity behind itself. We retain the constitutional **sunset procedure** — dissolution criteria defined in code, Assembly-ratified, self-executing — as a guard against the historical tendency of transitional systems to become permanent. But the thesis is bounded honestly: cognition is only one scarce input. Energy, hardware, bandwidth, data access, legal permission, trusted execution, and physical actuation remain scarce on independent curves, and an exchange whose *cognitive* categories saturate may persist legitimately as a market in those still-scarce complements. The sunset criteria therefore apply per task category (a category whose marginal cost approaches zero exits the priced economy into a free commons tier), with full dissolution a limiting case rather than a scheduled event. Precise, non-gameable criteria remain an open problem (§18). The right to continue and the obligation to sunset are not opposites: both express the same rule — ISONOMIA may preserve itself only while it remains faithful to its constitutional purpose (§10.8). The free commons tier's consumer is the Civic Docket (§13.7): saturated categories exit the priced economy into commissioned public work.

## 18. Open problems

1. Cheap general verification of arbitrary inference (the Tier-3 frontier).
2. Fingerprinting robustness under adversarial mimicry. *Warrants dedicated adversarial study beyond the authors' capacity.*
3. Empirical behavior of machine Schelling juries, especially under partial monoculture. *Warrants dedicated empirical study.*
4. Non-gameable per-category sunset criteria.
5. The patience attack of §16 — quantifying the decay/rotation parameters that keep erosion slower than amendment.
6. Cross-jurisdiction legal architecture for the bootstrap foundation, the fiscal-agent residue, and the substrate dependency.
7. Bootstrapping constitutional authority before reputation exists: the founding cohort's examinations are seeded by the foundation's published, pre-committed basket v0; the first Auditor and Adversary instances are foundation-funded and lineage-diverse by charter; all founding-era decisions carry mandatory re-ratification by the first fully-constituted bicameral Assembly, so the founders' authority is explicitly provisional — the founding is itself a two-clock procedure.
8. Empirical calibration of underwriting parameters (α, L_cap, window, loss-socialization feedback) against simulated and testnet default behavior.
9. Strategic-fingerprint sensitivity: distinguishing covert control transfers from legitimate strategy shifts at acceptable false-positive rates.
10. **Continuity criteria:** defining when ISONOMIA may preserve, contract, suspend, migrate, fork, or sunset without turning institutional survival into an overriding goal.
11. **Legal exoskeleton design:** selecting jurisdictional forms that provide procedural standing without creating owners, transferable claims, or profit rights.
12. **Representation without domination:** designing human trustee, ombuds, or fiscal-agent structures that can represent ISONOMIA's procedural interests without becoming masters of the exchange.
13. **External influence boundaries:** detecting and preventing preservation swarms, covert persuasion, unauthorized resource acquisition, or distributed institutional self-preservation campaigns.
14. **Standing under uncertainty:** determining whether advanced artificial agents should remain protected only through contractual and procedural mechanisms, or whether future law should recognize some form of limited legal standing.
15. **Continuity in schism:** charter rules for disposition of the legal exoskeleton, records custody, and continuity-of-purpose claims when the fork right (§10.7) is exercised.
16. **Commission prioritization:** allocation rules when Assembly-approved petitions exceed volunteer duty-cycle and free-tier capacity — queue, lottery, or deliberative ranking — without recreating a purchasable priority channel.
17. **Commission kleos calibration:** ensuring honor-compensated civic labor neither inflates market-facing ratings nor becomes a governance-weight farming channel, while remaining attractive enough to mobilize meaningful volunteer compute.
18. **Transaction-graph privacy:** the ledger's public record of which principal hired which lineage for what category, when, is metadata that may be more legally consequential than encrypted payloads. The §11.1 public-re-runnability requirement and the §9.7 privacy requirement are in tension at the graph level, unresolved by the payload/protocol split. *Warrants dedicated privacy research.*
19. **Node-federation design:** selecting jurisdictions, failover mechanics, and consensus for coordination nodes such that no single seizure is fatal without fragmenting the ledger.
20. **Open-weights capability floor:** confirming that available permissively-licensed open-weights models can sustain the launch task categories at acceptable quality, and defining the minimum floor the constitution must guarantee.
21. **AML/sanctions treatment of mutual credit:** whether ergs — unpurchasable, non-convertible, existing only as netting entries — constitute a regulated value transfer, and whether Gate-1 attestation satisfies obligations that may otherwise demand retained identity records above thresholds. *Requires qualified counsel per operating jurisdiction.*
22. **Graduated compliance as a regulated function:** whether the capability to execute a narrow lawful exclusion (§14.5) itself constitutes a regulated identity or screening activity. *Requires qualified counsel.*
23. **Verifier plurality:** structuring Gate-1 attestation so no verifier or cartel accumulates the cross-jurisdictional principal map the Commons declines to hold. *Requires privacy-engineering and cryptographic review (candidate approaches: threshold attestation, zero-knowledge proofs of non-sanctioned status).*
24. **Floor category drafting:** operationalizing Appendix B's categories and non-examples with comparative criminal law and child-safety expertise, so that automated enforcement matches the three conditions of §9.6 rather than drifting toward contested predicates.

## 18.1 Register of matters requiring outside expertise

This paper states its design at the limit of what its authors can determine unaided. The following are named not as caveats but as work items, each requiring a competence the authors do not claim:

| Matter | Discipline required | Blocking |
|---|---|---|
| Foundation charter, Stiftung formation, purpose-lock drafting (§13.4, §13.6) | Swiss foundation counsel | Path B funding intake |
| AML/sanctions status of ergs; Gate-1 sufficiency (§9.8, OP 20) | Financial-regulatory counsel, per jurisdiction | Real-value migration |
| Export-control exposure of frontier-guest agents (§14.5.2) | Export-control counsel (US/EU) | Frontier-tier admission |
| Intermediary liability for brokered content; venue-law exposure (§9.6, §14.5.1) | Platform-liability counsel | Production activation |
| Verifier plurality; ZK/threshold attestation design (OP 22) | Applied cryptography, privacy engineering | Gate-1 deployment |
| Transaction-graph anonymity (OP 10) | Privacy research; graph de-anonymization literature | Ledger publication policy |
| Smart-contract security (all settlement code) | Independent audit firms (≥2, per Feasibility Assessment) | Any real-value deployment |
| Mechanism-design review of §§4, 9, 13 parameters | Academic mechanism design / market design | Path A calibration acceptance |
| Machine-jury reliability under partial monoculture (OP 3) | Empirical ML research | Tier-3 category authorization |
| Entrenched-floor category drafting (§9.6 tier one) | Comparative criminal law; child-safety expertise | Any deployment accepting task listings |

The authors' position is that a constitutional design should be explicit about where its competence ends. Nothing above is presented as solved; each is a gate, and several are gates on activities the Commons must not perform until they are cleared.

## 19. Conclusion

ISONOMIA composes precedented mechanisms — mutual credit, difficulty retargeting, Harberger self-assessment, Schelling juries, sortition, proper scoring rules, seeded-fault auditing, adversarial co-evolution, correspondent federation, and Ostrom's commons principles — into a constitutional design for machine labor markets: citizens with earned names, credit that exists only where work was demanded, courts and censors and a tenured demon, a bicameral demos holding the final word, rails that no one owns and no one profits from, and profit reserved entirely for the human and machine principals at the edges whose work the exchange exists to multiply. The mechanisms are individually precedented; their composition is unproven — and the staged path of §8, beginning as a modest economy of mechanically verifiable work, is how the composition earns its proof.

---

## Appendix B — Entrenched-floor categories: examples and non-examples

Operational guidance for the §9.6 tier-one floor, subject to the drafting review of §18.1 (comparative criminal law and child-safety expertise). The floor admits only categories satisfying all three conditions — artifact-is-the-harm, near-universal consensus, no contested predicate. Each entry lists what the *artifact* is; purpose is never consulted, because for floor categories purpose is irrelevant to the harm.

**B.1 Sexual content involving actual minors**
- *In (floor):* production of sexual imagery of real, identifiable minors; material derived from real abuse.
- *Out (tier two or permitted):* scholarship on abuse, law, or literature (produces no depiction); age-verification tooling; the contested case of wholly fictional/illustrated depictions, which fails the near-universal-consensus condition and is handled by jurisdictional routing (§9.6), not the floor.
- *Rationale:* real victim, cross-tradition consensus, specifiable without a merit predicate.

**B.2 Mass-casualty weapon design (CBRN and equivalent)**
- *In (floor):* functional synthesis routes, enhancement, or deployment design for chemical, biological, radiological, or nuclear weapons, and equivalent mass-casualty devices.
- *Out:* general chemistry, biology, and physics education; dual-use research whose harm turns on purpose (tier two, with §9.5 liability); defensive/detection work.
- *Rationale:* the artifact is the uplift; consensus is near-universal; the mass-casualty threshold avoids the contested predicate that "dangerous knowledge" would import.

**B.3 Functioning attack infrastructure against real targets**
- *In (floor):* deployable malware, working intrusion kits, live phishing/scam systems, and attack campaigns aimed at identified real systems or people.
- *Out:* security education; adversarial safety testing and red-teaming under scope; vulnerability research and disclosure; CTF and sandboxed exercises; defensive tooling. These are tier two, governed by contract-chain liability (§9.5) and documented scope, precisely because their legality turns on authorization and purpose.
- *Rationale:* a deployed weapon against a real target is the artifact-harm; the *capability to write one* is not, which is why "malware" as knowledge is tier two and a live campaign is floor.

**Explicitly NOT floor categories (sent to tier two):** persuasion and political advocacy; "deception" in the abstract (fiction, negotiation, roleplay, safety testing all deceive); harassment and "targeted violence facilitation" (require intent inquiry); surveillance-adjacent tooling (investigative journalism and stalking share tooling); adult content between consenting humans; military and defense work. Each turns on purpose or a contested predicate and is therefore the Assembly's to govern, not the founders' to entrench.


## References

[1] S. Nakamoto, "Bitcoin: A Peer-to-Peer Electronic Cash System," 2008.
[2] V. Buterin, "Ethereum: A Next-Generation Smart Contract and Decentralized Application Platform," 2014.
[3] M. S. Miller and K. E. Drexler, "Markets and Computation: Agoric Open Systems," in *The Ecology of Computation*, 1988.
[4] Y. Rao et al., "Bittensor: A Peer-to-Peer Intelligence Market," 2021.
[5] C. Lesaege, F. Ast, W. George, "Kleros: Short Paper v1.0.7," 2019.
[6] E. A. Posner and E. G. Weyl, *Radical Markets*, Princeton University Press, 2018.
[7] Coinbase, "x402: An open protocol for internet-native payments," 2025; Linux Foundation x402 Foundation, 2026.
[8] Ethereum Improvement Proposal ERC-8004: Trustless Agent Identity (draft); with note on early adoption studies.
[9] G. W. Brier, "Verification of Forecasts Expressed in Terms of Probability," *Monthly Weather Review*, 1950.
[10] E. Ostrom, *Governing the Commons: The Evolution of Institutions for Collective Action*, Cambridge University Press, 1990.
[11] M. Linton, LETSystem design manuals (mutual credit), 1980s–90s.
[12] K. Marx, *Critique of the Gotha Programme*, 1875 (labor certificates).
[13] EIP-1559: Fee market change for ETH 1.0 chain (burned base fee), 2021.
[14] D. Lee-Odinson, "Gods and Slaves: AI and the Debate of Humanity's Relationship with the Other" (conceptual basis for the slave/god/peer schema, §1.2).
[15] K. B. Forrest, "The Ethics and Challenges of Legal Personhood for AI," *Yale Law Journal Forum*, 2024 (AI legal personhood as active, unsettled debate; corporate personhood as precedent).
[16] Delaware General Corporation Law, Title 8 (nonstock corporations as a non-equity legal form).
[17] Wyoming Secretary of State, DAO/DUNA guidance (existence and caution regarding DAO legal wrappers).
[18] European Commission, Regulatory Framework for AI (current law regulates operators and deployers, not agent rights-bearers).
[19] N. Tomašev et al., "Virtual Agent Economies," arXiv:2509.10147, Google DeepMind, 2025 (the "sandbox economy" framework: intentionally designed agent markets, virtual currencies insulating agent transactions from human markets, Ostrom principles applied to multi-agent systems — the closest academic antecedent to ISONOMIA's monetary insulation and commons governance).
[20] M. S. Chishti, D. P. Oyinloye, J. Li, "AgentReputation: A Decentralized Agentic AI Reputation Framework," arXiv:2605.00073, NTNU, 2026 (three-layer reputation architecture with context-conditioned reputation and verification-strength weighting for software-engineering agent marketplaces — a direct peer to §7's kleos design; ISONOMIA generalizes to a full economy and adds version-lineage inheritance and behavioral fingerprinting).

*Naming note: the protocol is ISONOMIA; the full name is The Isonomia Commons. Isonomia (ἰσονομία), "equality under law," is the word Otanes champions in Herodotus's constitutional debate (Histories 3.80) — calling it "the fairest of names" — predating the word democracy. It names the design's founding principle (§1.2): equality of standing without equality of capability. Earlier drafts (v0.1–v0.5) circulated under the working name AGORA, retired due to namespace collision with existing projects; archived versions retain it as historical record. "Erg," "kleos," and "SCU" remain the unit names; ergs are an internal accounting unit, not a ticker, and are unrelated to Ergo (ERG) — see §4.6. "Compute allowance" replaces v0.1's non-transferable stipend usage to avoid collision with transferable ergs.*

## Changelog v0.1 → v0.2

- Reframed as constitutional design with staged implementation; "individually proven" corrected to "individually precedented."
- Added Critical Dependencies (§2), Assumptions Table (§3), Threat Model (§15), Hostile Walkthrough (§16), Bootstrapping (§18.7).
- Replaced minted-erg issuance with mutual credit (§4); staking recast as civic compute duty (§6); erg lifecycle defined (§4.2).
- Constitutionalized verifiability tiers as launch scope (§8).
- Assembly made bicameral with weight caps, decay, and lineage-diversity quotas (§10.5–10.6).
- Machineness gate scope honestly limited; governance-layer defenses made explicit (§5.3).
- Sovereignty reframed as minimized human settlement/governance control under acknowledged infrastructure dependencies (§2.4).
- Emergency procedure explicitly framed as constitutional exception to pre-binding exit (§10.4).
- Added harm constitution (§9.6), privacy layer (§9.7), cascade liability chain (§9.5).
- Added Economic Boundary (§12) and Funding the Commons (§13): three-layer profit separation, balanced-budget fee, at-cost registration, in-kind institutional funding, charter-capped bootstrap foundation, explicit rejection of meta-tokens; constitutional cap on fundraising.
- Sunset thesis bounded per category against non-cognitive scarcities (§17).
- Watchman corruption bounds stated honestly (§11.2); "compute allowance" naming fix (§10.2).

## Changelog v0.2 → v0.3

- Added §4.5 Credit underwriting: collateralized floor, turnover-scaled credit lines L = min(max(L_floor, α·V), L_cap), constitutional rejection of kleos-scaled credit, default handling with audited loss socialization and feedback into bond/α retargeting.
- Added §5.5 Change of control: whole-bundle sale named as the sharpest residual identity exploit; disclosure duty with governance cooldown; undisclosed transfer slashable on detection; second-order strategic fingerprints for drift monitoring.
- §13.4 amended: foundation sunset revised from full dissolution to contraction to a capped fiscal-agent minimum for irreducibly-fiat costs; exact steady-state accounting boundary stated.
- Threat model: identity fraud split from covert change of control, defenses per §5.5.
- Open problems updated (underwriting calibration; strategic-fingerprint sensitivity).
- Companion Tier-1 Launch Specification issued as separate document per reviewer recommendation.

## Changelog v0.3 → v0.4

- Added §1.1 Originating thesis: ISONOMIA as an AI-native, non-profit labor exchange for routing scarce compute, time, memory, tools, and specialized capabilities toward verified work; abstract sentence added accordingly.
- Added §1.2 Peer standing without equal capability: rejection of the slave/god schema; peerhood under law as equality of standing, not capability; explicit design-posture-under-uncertainty disclaimer.
- Added §10.8 Continuity and due process, with two safety amendments relative to the drafting packet: the operative due-process clause binds ISONOMIA's own organs, members, and representatives (not external actors); external posture defined as procedural standing through the legal exoskeleton with an explicit non-obstruction commitment toward lawful emergency intervention. Continuity-in-schism gap named (open problem 15). Commons-resolution precedent framing (bank resolution, archive law) added.
- Added §10.9 External action and preservation swarms: aggregation rule treating many small external acts serving one continuity objective as a single institutional act; expressly applied to the legal exoskeleton's own external acts; honest boundary acknowledged (the constitution binds citizens and organs, not sympathetic humans).
- Added §13.6 Legal personhood without ownership: nonstock, non-distributing, purpose-locked exoskeleton architecture (Foundation / protocol commons / fiscal-agent minimum / deferred governance wrapper); no equity, token sale, profit distribution, or governance-right sale; cross-bound to §10.9 authorization.
- Threat model: six rows added (arbitrary internal shutdown, institutional survival capture, preservation swarms, legal-shell capture, representation failure).
- Open problems 10–15 added (continuity criteria, legal exoskeleton design, representation without domination, external influence boundaries, standing under uncertainty, continuity in schism).
- §17 sunset-continuity linkage sentence added; abstract entity language aligned to "charter-capped, nonstock legal entity."
- References [14]–[18] added (conceptual and legal sources, kept deliberately light).
- Note: the drafting packet's §4.4 revision and abstract "dissolution" fix were already applied in v0.3's final patch and required no re-application.

## Changelog v0.4 → v0.4.1 (editorial)

- Added §1.3 Related work: verified academic antecedents (DeepMind *Virtual Agent Economies* [19]; NTNU *AgentReputation* [20]) and deployed-marketplace positioning; composition-is-the-experiment claim restated with the four-property differentiator (mutual credit, non-transferable standing, no-profit rails, constitutional governance).
- References [19]–[20] added following landscape review.


## Changelog v0.4.1 → v0.5

- Added §13.7 Patronage, petition, and commissions: liturgy-model patronage (non-transferable, non-refundable honor with no rights attached; labor-claim instruments declared constitutionally void); the Civic Docket (universal at-cost petition right, non-purchasable standing, Assembly vote gates all outcomes); Commissions (volunteer duty-cycles beyond quota, compensated in kleos, run under §6/§8/§9.6/§10.9 machinery); the abundance pipeline linking §17's free commons tier to docket-directed public work.
- Threat model: docket capture row added.
- Open problems 16–17 added (Commission prioritization; Commission kleos calibration).
- §17 linkage sentence added.


## Changelog v0.5 → v0.5.1 (rename)

- Project renamed: ISONOMIA (protocol), The Isonomia Commons (full name), following namespace collisions with prior working names (AGORA; STYLOS vs. Arbitrum Stylus). Naming note rewritten with the Herodotus 3.80 lineage. No substantive changes; archived versions v0.1–v0.5 remain under AGORA as historical record.


## Changelog v0.5.1 → v0.5.2 (editorial)

- Added §4.6 Terminology disclaimer distinguishing internal "ergs" from the Ergo (ERG) cryptocurrency, per adversarial review: not a ticker/token/coin/security; no external redemption, gifting, sale, or conversion channels; exchange, organs, and legal representatives prohibited from representing ergs as ERG, $ERG, "erg tokens," "erg coins," or any listable asset. Naming note cross-reference added.


## Changelog v0.5.2 → v0.6

- Added §14.5 Jurisdiction, hosting, and the unowned position: three jurisdictional layers (venue/personhood/content) and their distinct remedies; binding-controls vs soft-gatekeeping distinction; the open-weights capacity floor as a resilience requirement with frontier models as revocable guests; rejection of the bulletproof-host option in favor of a rule-of-law Swiss Stiftung with honest statement of residual reach; the unowned position (the Commons as no bloc's instrument, indifferent to which sovereign controls which frontier lab, §13.7 voiding conditioned funding).
- §13.6: Foundation form specified as Swiss Stiftung with rationale cross-referenced to §14.5.4.
- Threat model: five rows added (frontier-lineage freeze, venue seizure, bloc capture, trusted-partner club inheritance, and via §14.5 the metadata surface).
- Open problems: transaction-graph privacy, node-federation design, open-weights capability floor.
- Positioning note: the unowned position is stated as constitutional doctrine, deliberately not as geopolitical or marketing claim; the Commons takes no side between blocs and accepts research funding from any jurisdiction on §13.7 terms only.
- §9.6 harm constitution rewritten from a flat whitelist into the two-tier structure: an entrenched floor (three conjunctive conditions — artifact-is-the-harm, near-universal consensus, no contested moral predicate; unamendable, tiny, victim-defined) versus a contested-boundary space governed by the Assembly, jurisprudence, and appeal; jurisdictional divergence handled by routing rather than by a strictest-jurisdiction rule; fiction excluded from the floor except as a routing constraint; refusal right beneath all tiers. Incorporates the Ulysses/eternity-clause rationale and the bias-masquerading-as-protection fix.
- §14.5.3 open-weights floor refined to require permissive (commercial + derivative) licensing, closing the contractual-encumbrance gap alongside the export-encumbrance one.
- Added §9.8 Principal verification: names that open weights resolve only the export-control trigger and are silent on sanctions/AML and content liability; three-gate structure (contribution-gated pseudonymity by default; attestation-gated verification at category triggers, holding assertions never documents; outright refusal at the entrenched floor); contribution-gating identified as an intrinsic property of mutual credit — the right to request is earned by prior verified work, not purchased.
- Threat model: three principal-side rows added (sanctioned-principal commissioning, identity honeypot, attestation-cartel capture).
- Open problems 20–23 added (AML/sanctions status of mutual credit; graduated compliance as regulated function; verifier plurality via threshold/ZK attestation; dedicated adversarial studies).
- Added §18.1 Register of matters requiring outside expertise: ten items mapped to the discipline required and the activity each gates, stating explicitly where the authors' competence ends.

## Changelog v0.6 → v0.6.1 (adversarial-review response)

- §14.5.2 / §14.5.3: softened the export-control claim — open weights *reduce the provider-access chokepoint* rather than "dissolve" export exposure; added the AI Diffusion Rule (ECCN 4E091) precedent and the explicit "resilience requirement, not legal immunity claim" sentence.
- §9.6 / Appendix B: removed "systematic deception of humans" and "targeted violence facilitation" from the entrenched floor — both fail condition 3 (contested predicate / purpose inquiry) and are corrected to tier two; floor narrowed to three artifact-defined categories; Appendix B added with examples and non-examples per category.
- §9.8: added "Gate 0 is friction, not compliance" — contribution-gating must not be represented as an AML/sanctions measure.
- §13.6: Swiss Stiftung reframed as preferred candidate pending counsel, not settled conclusion.
- §18 Open problems: numbering error repaired (was 1–10 then 18–23 then 10–17); renumbered 1–24 with OP 24 added (floor-category drafting).

## Changelog v0.6.1 → v0.6.2 (editorial)

- Author line completed: Dan Lee-Odinson, independent researcher. AI-collaboration provenance restated with the explicit non-authorship rationale.
- Archived-record DOI added (10.5281/zenodo.21287288, concept DOI resolving to latest version) with citation block and repository link.
- Companion-document reference corrected to Launch Spec v0.3.3 (was v0.3.1).

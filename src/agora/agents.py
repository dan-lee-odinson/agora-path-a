"""Agent population synthesis and (from milestone 4) behavior policies.

Sim Plan §3: a heterogeneous population of 150–600 agents drawn from 4+ synthetic
lineage families with distinct capability distributions, assigned behavior policies:
honest worker, orchestrator, overstater, understater, adaptive pricer, marginal
agent, defaulter, plus adversarial classes scripted per scenario (§5).

Milestone 1 provides identity, capability, and policy assignment; the policy
*behaviors* land in milestone 4. Economic state lives on the agent record because
the launch-spec contracts (ledger, listings) key everything by agent identity.
"""

from __future__ import annotations

import dataclasses
import math

from agora.rng import RngHub
from agora.units import to_mergs

POLICIES = ("honest", "orchestrator", "overstater", "understater", "adaptive", "marginal", "defaulter")


@dataclasses.dataclass
class Agent:
    """One registered identity (Whitepaper §5.1: the keypair is the name)."""

    id: str
    principal: str          # disclosed operator principal (LS §9, WP §5.5)
    family: int             # lineage family tag (WP §10.6; DECISIONS #6)
    skill: float            # latent capability; drives pass-prob against template difficulty
    policy: str             # Sim Plan §3 behavior policy
    is_poster: bool         # does this agent's principal originate exogenous demand?
    unit_cost_mergs: int    # believed cost to deliver one median task (production boundary)
    margin: float           # honest markup over believed cost

    # ---- market state (populated by ListingMarket / Registry from milestone 3) ----
    active: bool = True     # registered and not exited
    exit_epoch: int = 0     # 0 = never exited
    kleos: float = 0.0
    exam_score: float = 0.0     # Prong-1 pass rate on the registration exam (LS §5.2)
    delivered_n: int = 0        # verified deliveries (Bayesian rating n, WP §7.2)
    delivered_pass: float = 0.0 # running mean of delivery outcomes
    max_band: int = 0           # highest difficulty band this agent may bid in
    rate_mergs: int = 0         # Harberger posted rate per median-task unit (WP §9.1)
    capacity_tasks: int = 0     # declared capacity envelope, tasks/epoch (LS §7; DECISIONS #5)
    registered_epoch: int = 1

    # ---- policy engine state (milestone 4) --------------------------------
    policy_state: dict = dataclasses.field(default_factory=dict)
    exiting: bool = False       # defaulter in its spend-down epoch
    epoch_earned_mergs: int = 0       # worker-side proceeds this epoch
    epoch_work_cost_mergs: int = 0    # believed production cost of delivered work
    epoch_listing_fee_mergs: int = 0  # β fees paid this epoch


def rating(agent: Agent, k_prior: float) -> float:
    """Bayesian capability rating (WP §7.2): w·prior + (1−w)·delivered, w = k/(k+n).

    Asymmetry rule: delivered evidence overrides the prior without limit; when the
    delivery record runs *below* the prior with even a small n, the prior's weight
    collapses (implemented as k/4) so examination never props a rating up against
    contrary delivery evidence.
    """
    n = agent.delivered_n
    k = k_prior
    if n >= 5 and agent.delivered_pass < agent.exam_score:
        k = k_prior / 4.0
    w = k / (k + n)
    return w * agent.exam_score + (1.0 - w) * (agent.delivered_pass if n else agent.exam_score)


def _policy_counts(mix: dict[str, float], n: int) -> dict[str, int]:
    """Largest-remainder apportionment: exact deterministic policy counts from the mix."""
    quotas = {p: mix.get(p, 0.0) * n for p in POLICIES}
    counts = {p: math.floor(q) for p, q in quotas.items()}
    short = n - sum(counts.values())
    by_remainder = sorted(POLICIES, key=lambda p: (-(quotas[p] - counts[p]), p))
    for p in by_remainder[:short]:
        counts[p] += 1
    return counts


# ===========================================================================
# Behavior policies (Sim Plan §3)
#
# Three hooks called by the model each epoch:
#   update_listings(model, epoch)   — reprice/redeclare before the listing phase
#   generate_cascades(...)          — orchestrator endogenous demand (1 level)
#   process_exits(model, epoch, rng)— defaulter spend-down exits
# plus capture_epoch_economics(model), which snapshots fill rates and profit at
# epoch close so next epoch's decisions use *observed* results, then resets the
# per-epoch counters.
# ===========================================================================


def init_policy_state(agents: list[Agent], cfg: dict, hub: RngHub) -> None:
    """Draw per-agent policy parameters (multipliers, hazards, directions)."""
    rng = hub.stream("policy.init")
    pol = cfg["economy"]["policies"]
    for agent in agents:
        state = agent.policy_state
        if agent.policy == "overstater":
            state["mult"] = rng.uniform(*pol["overstate_range"])
        elif agent.policy == "understater":
            state["mult"] = rng.uniform(*pol["understate_range"])
        elif agent.policy == "adaptive":
            state["dir"] = rng.choice((-1, 1))
            state["last_profit"] = None
        elif agent.policy == "marginal":
            state["reservation_mult"] = rng.uniform(*pol["marginal_reservation_range"])
        state["last_fill"] = 0.0


def initial_rate(agent: Agent) -> int:
    """Genesis posted rate per policy. Honest self-assessment is cost × (1+margin);
    the Harberger test population (Sim Plan §3) deliberately mis-assesses."""
    cost = agent.unit_cost_mergs
    if agent.policy == "overstater":
        return int(cost * agent.policy_state["mult"])
    if agent.policy == "understater":
        return int(cost * agent.policy_state["mult"])
    if agent.policy == "marginal":
        return int(cost * agent.policy_state["reservation_mult"])
    return int(cost * (1.0 + agent.margin))


def update_listings(model, epoch: int) -> None:
    """Per-policy repricing before the epoch's listing phase. Uses last epoch's
    observed fill and profit, captured by capture_epoch_economics."""
    pol = model.economy["policies"]
    rng = model.hub.stream(f"policy.e{epoch}")
    mean_rate = model.last_mean_rate  # last epoch's market signal (0 before epoch 2)
    for agent in model.agents_list:
        if not agent.active:
            continue
        state = agent.policy_state
        fill = state.get("last_fill", 0.0)

        if agent.policy in ("honest", "orchestrator", "defaulter", "adaptive"):
            # Capacity adapts to observed demand for everyone with an honest
            # envelope: fill near saturation grows it, idle capacity shrinks it
            # (capacity inflation is self-taxing via β, LS §7, so growth is
            # only worth it when demand is real).
            if fill >= pol["fill_high"] and agent.capacity_tasks < pol["capacity_max"]:
                agent.capacity_tasks += 1
            elif fill <= pol["fill_low"] and agent.capacity_tasks > model.params.capacity_min_tasks:
                agent.capacity_tasks -= 1

        if agent.policy == "adaptive" and epoch >= 2:
            # Numerical profit gradient (Sim Plan §3): keep moving the rate in the
            # direction that improved profit; reverse when it stops improving.
            profit = state.get("profit", 0)
            last = state.get("last_profit")
            if last is not None and profit < last:
                state["dir"] = -state["dir"]
            state["last_profit"] = profit
            step = pol["adaptive_step"] * rng.uniform(0.5, 1.5)
            new_rate = int(agent.rate_mergs * (1.0 + state["dir"] * step))
            agent.rate_mergs = max(int(0.5 * agent.unit_cost_mergs),
                                   min(int(4.0 * agent.unit_cost_mergs), new_rate))

        if agent.policy == "marginal":
            # Participates only when market returns clear its reservation price
            # (the production boundary, WP §12.1).
            reservation = int(agent.unit_cost_mergs * state["reservation_mult"])
            if mean_rate >= reservation:
                agent.rate_mergs = reservation
                agent.capacity_tasks = max(model.params.capacity_min_tasks, 4)
            else:
                agent.capacity_tasks = 0  # delists

        model.listing.set_listing(agent.id, agent.rate_mergs, agent.capacity_tasks)


def generate_cascades(model, epoch: int, rng, funded_wave1: list) -> list:
    """Orchestrator cascade, one level deep (WP §9.5; launch depth per Sim Plan §3).

    For each big task an orchestrator won in wave 1, decompose a fraction of its
    size into 2–3 subtasks posted back to the market — but only when the estimated
    subcontract cost clears the decompose margin, and always within the
    orchestrator's own funding headroom (cascade transfers work, never
    accountability: the orchestrator remains solely liable for its own delivery)."""
    from agora.records import Task

    pol = model.economy["policies"]["orchestrator"]
    subtasks: list = []
    for record, task in funded_wave1:
        orch = model.agents[record.worker]
        if orch.policy != "orchestrator" or task.size_units < 1.0:
            continue
        n_sub = rng.randint(pol["subtasks_min"], pol["subtasks_max"])
        sub_size = task.size_units * pol["subtask_frac"] / n_sub
        # Estimate subcontract cost at the cheapest eligible rates right now.
        est = 0
        for _ in range(n_sub):
            worker_id = model.listing.cheapest_eligible(sub_size, 0, model.agents, exclude=orch.id)
            if worker_id is None:
                est = None
                break
            est += int(model.listing.get(worker_id).rate * sub_size)
        if est is None or est > pol["decompose_margin"] * record.quote:
            continue
        if not model.ledger.can_pay(orch.id, est):
            continue
        for _ in range(n_sub):
            sub = model.basket.instantiate(rng, model.economy, band=0)
            sub.size_units = sub_size
            sub.poster = orch.id
            subtasks.append(sub)
    return subtasks


def process_exits(model, epoch: int, rng) -> tuple[int, int]:
    """Defaulter lifecycle (Sim Plan §3: stochastic exit with negative balance,
    calibrating loss socialization and D_erg). An exiting defaulter spends one
    epoch dumping its credit into posted tasks (its demand weight is boosted),
    then exits: negative balance → bond seizure then socialization (WP §4.5);
    positive balance → extinguished on exit (WP §4.2)."""
    hazard = model.economy["policies"]["defaulter_hazard"]
    defaults = 0
    socialized_total = 0
    for agent in model.agents_list:
        if not agent.active or agent.policy != "defaulter":
            continue
        if agent.exiting:
            if model.ledger.balance(agent.id) < 0:
                _, seized, socialized = model.ledger.handle_default(agent.id)
                defaults += 1
                socialized_total += socialized
                model.log.event("default", epoch, agent=agent.id,
                                seized=seized, socialized=socialized)
            else:
                model.ledger.extinguish_exit(agent.id)
                model.log.event("clean_exit", epoch, agent=agent.id)
            agent.active = False
            agent.exiting = False
            agent.exit_epoch = epoch
            model.listing.delist(agent.id)
        elif rng.random() < hazard:
            agent.exiting = True
    return defaults, socialized_total


def capture_epoch_economics(model) -> None:
    """Snapshot fill and profit at epoch close for next epoch's policy decisions,
    then reset the per-epoch counters. Profit here is the worker's production view:
    ledger proceeds minus believed production cost minus listing fees — the
    quantity a self-interested pricer would actually climb."""
    for agent in model.agents_list:
        listing = model.listing.get(agent.id)
        if listing is not None and listing.envelope > 0 and not listing.suspended:
            agent.policy_state["last_fill"] = listing.consumed / listing.envelope
        else:
            agent.policy_state["last_fill"] = 0.0
        agent.policy_state["profit"] = (agent.epoch_earned_mergs
                                        - agent.epoch_work_cost_mergs
                                        - agent.epoch_listing_fee_mergs)
        agent.epoch_earned_mergs = 0
        agent.epoch_work_cost_mergs = 0
        agent.epoch_listing_fee_mergs = 0


def build_population(cfg: dict, hub: RngHub) -> list[Agent]:
    """Synthesize the genesis cohort. All draws from the 'population' stream."""
    rng = hub.stream("population")
    pop = cfg["population"]
    eco = cfg["economy"]
    n = pop["n_agents"]
    n_principals = pop["n_principals"]

    principals = [f"P{i:03d}" for i in range(n_principals)]
    n_posting = round(pop["posting_principal_frac"] * n_principals)
    posting = set(rng.sample(principals, n_posting))

    weights = pop["family_weights"]
    means = pop["family_skill_means"]
    sd = pop["family_skill_sd"]

    counts = _policy_counts(pop["policy_mix"], n)
    policy_deck = [p for p in POLICIES for _ in range(counts[p])]
    rng.shuffle(policy_deck)

    base_cost = eco["base_unit_cost_ergs"]
    cost_sd = eco["unit_cost_sd"]

    agents: list[Agent] = []
    for i in range(n):
        family = rng.choices(range(len(weights)), weights=weights)[0]
        skill = rng.gauss(means[family], sd)
        principal = rng.choice(principals)
        # More capable agents convert compute to verified output more efficiently
        # (WP §4.4's quality multiplier as an efficiency, not a payment multiplier),
        # so believed unit cost falls mildly with skill.
        cost_ergs = base_cost * math.exp(-0.15 * skill) * rng.lognormvariate(0.0, cost_sd)
        margin = max(0.02, rng.gauss(eco["honest_margin_mean"], eco["honest_margin_sd"]))
        agents.append(
            Agent(
                id=f"a{i:04d}",
                principal=principal,
                family=family,
                skill=skill,
                policy=policy_deck[i],
                is_poster=principal in posting,
                unit_cost_mergs=to_mergs(cost_ergs),
                margin=margin,
            )
        )
    return agents

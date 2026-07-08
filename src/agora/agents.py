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

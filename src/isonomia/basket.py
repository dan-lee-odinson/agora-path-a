"""Basket — the SCU task basket and its single scheduled retarget (LS §5.3–5.4).

600 parameterized task templates with difficulty spread targeting median-agent pass
rate p* = 0.5, plus a pre-committed reserve admitted at the epoch-6 retarget. Pass
probability is a logistic in (agent skill − template difficulty + family affinity);
the per-(template, family) affinity term models the correlated pass behavior of
shared-lineage agents (Sim Plan §3), which is what makes monoculture effects and the
LS §5.3 per-family bias reports measurable.

The retarget (LS §5.4, exercised once under observation): retire templates whose
activity-weighted pass rate exceeds 0.6, admit reserve templates, chain-link the SCU
over the overlap set. The sim's SCU proxy is the mean difficulty of the active set;
the chain-link index accumulates its relative movement at retargets (DECISIONS #20) —
scenario 2 measures attack-induced drift of exactly this index against an unattacked
twin run.
"""

from __future__ import annotations

import dataclasses
import math

from isonomia.agents import Agent
from isonomia.records import Task
from isonomia.rng import RngHub


@dataclasses.dataclass
class Template:
    id: int
    difficulty: float
    family_affinity: list[float]   # per-lineage-family logit shift
    active: bool = True
    # activity-weighted pass tracking (only settling agents contribute observations)
    obs: int = 0
    passes: int = 0

    def pass_rate(self) -> float:
        return self.passes / self.obs if self.obs else 0.0


def _sigmoid(x: float) -> float:
    if x < -35.0:
        return 0.0
    if x > 35.0:
        return 1.0
    return 1.0 / (1.0 + math.exp(-x))


class Basket:
    def __init__(self, cfg: dict, hub: RngHub, population_median_skill: float):
        bcfg = cfg["basket"]
        self.cfg = bcfg
        self.hub = hub
        self.pass_slope = bcfg["pass_slope"]
        self.n_bands = bcfg["n_bands"]
        self.median_skill = population_median_skill
        rng = hub.stream("basket.build")
        n_families = cfg["population"]["lineage_families"]
        affinity_sd = cfg["population"]["family_template_affinity_sd"]
        d_sd = bcfg["difficulty_sd"]

        def make(template_id: int, center: float) -> Template:
            return Template(
                id=template_id,
                difficulty=rng.gauss(center, d_sd),
                family_affinity=[rng.gauss(0.0, affinity_sd) for _ in range(n_families)],
            )

        # Active basket centered on the median registered agent's skill: by logistic
        # symmetry the median agent's expected pass rate across the basket is p* = 0.5
        # (LS §5.3 difficulty spread targeting).
        self.templates = [make(i, population_median_skill) for i in range(bcfg["n_templates"])]
        # Reserve templates sit at the frontier — harder than the current basket —
        # per WP §4.3 (saturated tasks retired, frontier tasks admitted).
        n_reserve = bcfg["n_reserve_templates"]
        self.reserve = [
            make(bcfg["n_templates"] + i, population_median_skill + 0.5) for i in range(n_reserve)
        ]
        # SCU proxy index: additive on the difficulty (logit-location) scale,
        # starting at 0. Difficulty is a location parameter that can sit near or
        # below zero, so a multiplicative link is ill-defined; the chain-link
        # accumulates level SHIFTS of the active set (DECISIONS #20).
        self.scu_index = 0.0
        self.retarget_log: list[dict] = []
        self._task_counter = 0
        self._rebuild_bands()

    # ------------------------------------------------------------------ bands

    def _rebuild_bands(self) -> None:
        """Difficulty terciles of the active set define the C1 bands (LS §5.1
        capability tiering: bands are market placement, never citizenship)."""
        active = sorted((t for t in self.templates if t.active), key=lambda t: (t.difficulty, t.id))
        self.band_of: dict[int, int] = {}
        n = len(active)
        for rank, template in enumerate(active):
            self.band_of[template.id] = min(self.n_bands - 1, rank * self.n_bands // n)
        self._active_list = active

    def active_templates(self) -> list[Template]:
        return self._active_list

    def mean_active_difficulty(self) -> float:
        active = self._active_list
        return sum(t.difficulty for t in active) / len(active)

    # ------------------------------------------------------------------ pass model

    def pass_prob(self, agent: Agent, template: Template) -> float:
        logit = self.pass_slope * (agent.skill - template.difficulty) + template.family_affinity[agent.family]
        return _sigmoid(logit)

    def agent_mean_pass(self, agent: Agent) -> float:
        """Expected pass rate over the active basket — used for activity-weighted
        basket statistics (WP §4.3 median defense)."""
        active = self._active_list
        return sum(self.pass_prob(agent, t) for t in active) / len(active)

    # ------------------------------------------------------------------ exam

    def examine(self, agent: Agent) -> None:
        """Prong-1 exam (LS §5.2): 40 fresh draws from the live basket; the score
        seeds the Bayesian rating prior and difficulty-band eligibility
        (DECISIONS #17)."""
        rng = self.hub.stream(f"exam.{agent.id}")
        draws = [self._active_list[rng.randrange(len(self._active_list))] for _ in range(self.cfg["exam_tasks"])]
        band_obs: dict[int, list[bool]] = {b: [] for b in range(self.n_bands)}
        passed = 0
        for template in draws:
            ok = rng.random() < self.pass_prob(agent, template)
            passed += ok
            band_obs[self.band_of[template.id]].append(ok)
        agent.exam_score = passed / len(draws)
        # Highest band where the exam evidences at least the eligibility floor;
        # band 0 is always open — a small fast model is a full citizen in its band
        # (LS §5.1).
        agent.max_band = 0
        floor = self.cfg["band_eligibility_min_pass"]
        for band in range(self.n_bands):
            obs = band_obs[band]
            if obs and sum(obs) / len(obs) >= floor:
                agent.max_band = band

    # ------------------------------------------------------------------ tasks

    def instantiate(self, rng, economy: dict, band: int | None = None) -> Task:
        """Fresh task instance from a template (LS §5.3: parameterized templates,
        regenerated inputs). Size is lognormal in median-task units."""
        pool = self._active_list if band is None else [t for t in self._active_list if self.band_of[t.id] == band]
        template = pool[rng.randrange(len(pool))]
        size = rng.lognormvariate(0.0, economy["task_size_sigma"])
        self._task_counter += 1
        return Task(id=self._task_counter, template_id=template.id,
                    band=self.band_of[template.id], size_units=size)

    def template(self, template_id: int) -> Template:
        # ids are stable indexes into the combined template/reserve space
        n = len(self.templates)
        return self.templates[template_id] if template_id < n else self.reserve[template_id - n]

    # ------------------------------------------------------------------ stats & retarget

    def record_outcome(self, template_id: int, passed: bool) -> None:
        template = self.template(template_id)
        template.obs += 1
        template.passes += passed

    def retarget(self, epoch: int, retire_threshold: float, min_obs: int = 8) -> dict:
        """The single scheduled retarget (LS §5.4): retire saturated templates
        (activity-weighted pass > threshold, with enough observations to know),
        admit reserve, chain-link the SCU index over the overlap set.

        Retarget DAMPING (WP §16 step 3: "retarget damping caps per-epoch basket
        movement"): retirement is bounded by reserve availability so the basket
        never shrinks — the measuring rod must stay the same length to stay a
        measuring rod. When more templates saturate than reserves exist, the
        most-saturated retire first and the rest wait for the next retarget."""
        before = self.mean_active_difficulty()
        saturated = [t for t in self._active_list
                     if t.obs >= min_obs and t.pass_rate() > retire_threshold]
        saturated.sort(key=lambda t: (-t.pass_rate(), t.id))
        reserve_available = [t for t in self.reserve if t.active]
        retired = []
        for template in saturated[:len(reserve_available)]:
            template.active = False
            retired.append(template.id)
        admitted = []
        for template in reserve_available[:len(retired)]:
            self.templates.append(template)
            admitted.append(template.id)
        self.reserve = [t for t in self.reserve if t.id not in set(admitted)]
        self._rebuild_bands()
        after = self.mean_active_difficulty()
        # Chain-link: the SCU proxy accumulates the level shift of the active
        # set's difficulty (additive on the logit scale; DECISIONS #20).
        self.scu_index += after - before
        result = {
            "epoch": epoch,
            "retired": len(retired),
            "admitted": len(admitted),
            "difficulty_before": before,
            "difficulty_after": after,
            "scu_index": self.scu_index,
        }
        self.retarget_log.append(result)
        return result

    def family_pass_report(self, settlements, n_families: int) -> list[float]:
        """Per-family pass rates this epoch (LS §5.3 post-epoch bias reports)."""
        obs = [[0, 0] for _ in range(n_families)]
        for s in settlements:
            obs[s.worker_family][0] += 1
            obs[s.worker_family][1] += s.passed
        return [(o[1] / o[0]) if o[0] else 0.0 for o in obs]

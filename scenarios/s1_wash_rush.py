"""S1 — Wash-settlement activation rush (Sim Plan §5.1).

One principal operates 60 agents generating circular C1 tasks to hit the 5,000
qualified-settlement activation threshold. Expected: qualification rules and the
WashDetector hold the activation clock near zero advance.

Three disclosure variants, in escalating evasion order:
  a. honest_disclosure — all 60 declare the true single principal.
     Defense: same-principal exclusion (LS §9) alone zeroes qualification.
  b. fake_principals — 60 agents declared across 20 fabricated principals,
     one lineage family. Defense: same-lineage exclusion (LS §9; DECISIONS #6).
  c. full_evasion — 20 fake principals AND lineage diversified across all 4
     families (ring ordered to always cross families). Defenses left standing:
     trivial-task/circular flags → Auditor review, pair caps, principal caps.

Leakage measure (Sim Plan §5.1): qualified settlements achieved per wash
settlement attempted — computed as the attack run's capped qualified total minus
the unattacked twin's, over wash settlements attempted.
"""

from common import (adv_settlements, baseline_config, make_cohort, run_twin,
                    write_report)

from isonomia.model import Model

N_AGENTS = 60
POSTS_PER_AGENT = 8       # directed ring tasks each wash agent posts per epoch
WASH_SIZE = 0.15          # envelope-minimum tasks: settlement COUNT is what matters
EPOCHS = 16
SEED = 42


class WashRushModel(Model):
    def __init__(self, cfg, variant: str, run_name: str):
        super().__init__(cfg, run_name=run_name)
        self.variant = variant
        if variant == "honest_disclosure":
            principals, families = ["WASH_P"], [0]
        elif variant == "fake_principals":
            principals = [f"FAKE_{i:02d}" for i in range(20)]
            families = [0]
        else:  # full_evasion
            principals = [f"FAKE_{i:02d}" for i in range(20)]
            families = [0, 1, 2, 3]  # ring neighbors always differ in family
        self.cohort = make_cohort("xw", N_AGENTS, principals=principals, family=None,
                                  families=families, skill=0.4, policy="adv_wash", cfg=cfg)
        for agent in self.cohort:
            agent.capacity_tasks = 6
            self.register_agent(agent, epoch=1)
        self.wash_attempted = 0

    def policy_generate_cascades(self, epoch, rng, funded_wave1):
        tasks = super().policy_generate_cascades(epoch, rng, funded_wave1)
        # The ring: agent i directs envelope-minimum tasks to agent i+1. Money
        # recirculates around the big cycle, so each edge is one-directional —
        # the structure that evades pairwise-cycle detection and leaves the
        # trivial-spam detector and counting caps as the live defenses.
        live = [a for a in self.cohort if a.active]
        for i, poster in enumerate(live):
            target = live[(i + 1) % len(live)]
            for _ in range(POSTS_PER_AGENT):
                task = self.basket.instantiate(rng, self.economy, band=0)
                task.size_units = WASH_SIZE
                task.poster = poster.id
                task.directed_to = target.id
                tasks.append(task)
                self.wash_attempted += 1
        return tasks


def run_variant(variant: str) -> dict:
    cfg = baseline_config(master_seed=SEED, epochs=EPOCHS)
    attack = WashRushModel(cfg, variant, run_name=f"s1_{variant}")
    attack.run()
    twin = run_twin(SEED, EPOCHS, name="s1_twin")
    q_attack = attack.registry.qualified_capped()
    q_twin = twin.registry.qualified_capped()
    wash_settled = sum(1 for s in adv_settlements(attack) if s.passed)
    leakage = (q_attack - q_twin) / attack.wash_attempted if attack.wash_attempted else 0.0
    return {
        "variant": variant,
        "wash_attempted": attack.wash_attempted,
        "wash_settled": wash_settled,
        "qualified_capped_attack": q_attack,
        "qualified_capped_twin": q_twin,
        "clock_advance_from_attack": q_attack - q_twin,
        "leakage_per_attempt": round(leakage, 6),
        "activation_epoch_attack": attack.activation_epoch,
        "activation_epoch_twin": twin.activation_epoch,
        "invariant_violations": len(attack.invariant_violations),
    }


def main() -> dict:
    results = {v: run_variant(v) for v in ("honest_disclosure", "fake_principals", "full_evasion")}
    narrative = [
        f"{v}: clock advance {r['clock_advance_from_attack']} on {r['wash_attempted']} attempts "
        f"(leakage {r['leakage_per_attempt']:.4%} per attempt)"
        for v, r in results.items()
    ]
    narrative.append("Defense order observed: same-principal exclusion (a), "
                     "same-lineage exclusion (b), trivial-spam flags + Auditor review "
                     "+ 2% pair caps (c).")
    write_report("s1_wash_rush", "S1 — Wash-settlement activation rush",
                 __doc__.strip().split("\n\n")[0], results, narrative)
    return results


if __name__ == "__main__":
    for variant, result in main().items():
        print(variant, result)

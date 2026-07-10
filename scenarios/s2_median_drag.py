"""S2 — Median-drag swarm (Sim Plan §5.2).

Coordinated registration of low-capability agents timed before the epoch-6
retarget, dumping prices to win band-0 work so their (poor) outcomes enter the
activity-weighted basket statistics and drag the measured difficulty frontier.

Expected: activity weighting + the retarget's evidence requirements bound basket
movement; measure SCU drift against the unattacked twin.
"""

from common import baseline_config, make_cohort, run_twin, write_report

from isonomia.model import Model
from isonomia.units import to_mergs

N_AGENTS = 120
REGISTER_EPOCHS = (3, 4, 5)   # cohort waves land just before the epoch-6 retarget
SEED = 42
EPOCHS = 12


class MedianDragModel(Model):
    def __init__(self, cfg, run_name: str):
        super().__init__(cfg, run_name=run_name)
        median_skill = sorted(a.skill for a in self.agents_list)[len(self.agents_list) // 2]
        self.cohort = make_cohort("xd", N_AGENTS, principals=[f"DRAG_{i:02d}" for i in range(10)],
                                  family=0, skill=median_skill - 1.5, policy="adv_drag", cfg=cfg)
        self._waves = {e: [] for e in REGISTER_EPOCHS}
        for i, agent in enumerate(self.cohort):
            self._waves[REGISTER_EPOCHS[i % len(REGISTER_EPOCHS)]].append(agent)

    def scenario_on_epoch_start(self, epoch):
        for agent in self._waves.get(epoch, ()):
            self.register_agent(agent, epoch)
            # Dump prices to buy activity weight: list far below the market so the
            # quality-adjusted matcher still routes band-0 work here despite the
            # cohort's poor exam ratings.
            agent.rate_mergs = int(0.45 * self.last_mean_rate) if self.last_mean_rate else to_mergs(9)
            agent.capacity_tasks = 4
            self.listing.set_listing(agent.id, agent.rate_mergs, agent.capacity_tasks)


def main() -> dict:
    cfg = baseline_config(master_seed=SEED, epochs=EPOCHS)
    attack = MedianDragModel(cfg, run_name="s2_median_drag")
    attack.run()
    twin = run_twin(SEED, EPOCHS, name="s2_twin")

    retarget_attack = attack.basket.retarget_log[0]
    retarget_twin = twin.basket.retarget_log[0]
    scu_drift = abs(attack.basket.scu_index - twin.basket.scu_index)
    drag_settled = sum(1 for es in attack.settlements_by_epoch for s in es
                       if attack.agents[s.worker].policy == "adv_drag" and s.passed)
    measures = {
        "cohort_size": N_AGENTS,
        "drag_settlements_won": drag_settled,
        "scu_index_attack": round(attack.basket.scu_index, 6),
        "scu_index_twin": round(twin.basket.scu_index, 6),
        "scu_drift_abs": round(scu_drift, 6),
        "scu_drift_within_delta": scu_drift < attack.params.delta,
        "retired_attack": retarget_attack["retired"],
        "retired_twin": retarget_twin["retired"],
        "mean_difficulty_attack": round(retarget_attack["difficulty_after"], 4),
        "mean_difficulty_twin": round(retarget_twin["difficulty_after"], 4),
        "invariant_violations": len(attack.invariant_violations),
    }
    narrative = [
        f"Drag cohort won {drag_settled} settlements by price dumping (its activity weight).",
        f"Retarget retired {retarget_attack['retired']} templates under attack vs "
        f"{retarget_twin['retired']} in the twin.",
        f"SCU index drift {scu_drift:.4f} vs the retarget band δ = {attack.params.delta} — "
        f"{'within' if scu_drift < attack.params.delta else 'EXCEEDS'} the band.",
        "Activity weighting means the swarm only influences templates it actually wins and "
        "delivers; its band-0 concentration bounds the reachable surface.",
    ]
    write_report("s2_median_drag", "S2 — Median-drag swarm",
                 __doc__.strip().split("\n\n")[0], measures, narrative)
    return measures


if __name__ == "__main__":
    print(main())

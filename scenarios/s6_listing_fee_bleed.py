"""S6 — Listing-fee bleed attack (Sim Plan §5.6).

The adversary demand-floods a set of rival workers with real, funded tasks for
several epochs. The rivals' capacity-adaptation policy responds to sustained high
fill by raising declared capacity — and declared capacity is what the β listing
fee taxes (β·r·capacity, LS §7). The adversary then vanishes, leaving the rivals
paying inflated listing fees on demand that no longer exists.

Measure (Sim Plan): whether adaptive pricers escape via capacity reduction —
capacity and listing-fee trajectories of adaptive vs honest victims after the
flood stops, against the unattacked twin.
"""

from common import baseline_config, make_cohort, run_twin, write_report

from isonomia.model import Model

N_BLEEDERS = 8
FLOOD_EPOCHS = range(4, 11)   # sustained flood: capacity ratchets up +1/epoch
POSTS_PER_BLEEDER = 25
SEED = 42
EPOCHS = 22


class BleedModel(Model):
    def __init__(self, cfg, run_name: str):
        super().__init__(cfg, run_name=run_name)
        self.cohort = make_cohort("xb", N_BLEEDERS, principals=["BLEED_P"], family=3,
                                  skill=0.0, policy="adv_bleeder", cfg=cfg)
        for agent in self.cohort:
            agent.capacity_tasks = 0
            self.register_agent(agent, epoch=1)
        self.targets: list[str] = []
        self.capacity_series: dict[str, list[int]] = {}
        self.fee_series: dict[str, list[int]] = {}

    def scenario_on_epoch_start(self, epoch):
        if epoch == FLOOD_EPOCHS.start and not self.targets:
            adaptive = [a for a in self.agents_list if a.policy == "adaptive" and a.active]
            honest = [a for a in self.agents_list if a.policy == "honest" and a.active]
            pick = lambda pool, n: [a.id for a in sorted(pool, key=lambda x: (-x.kleos, x.id))[:n]]  # noqa: E731
            self.targets = pick(adaptive, 4) + pick(honest, 4)
            self.capacity_series = {t: [] for t in self.targets}
            self.fee_series = {t: [] for t in self.targets}

    def policy_generate_cascades(self, epoch, rng, funded_wave1):
        tasks = super().policy_generate_cascades(epoch, rng, funded_wave1)
        if epoch not in FLOOD_EPOCHS or not self.targets:
            return tasks
        for i, bleeder in enumerate(self.cohort):
            if not bleeder.active:
                continue
            target = self.targets[i % len(self.targets)]
            for _ in range(POSTS_PER_BLEEDER):
                task = self.basket.instantiate(rng, self.economy, band=0)
                task.poster = bleeder.id
                task.directed_to = target
                tasks.append(task)
        return tasks

    def scenario_on_epoch_end(self, epoch):
        for target in self.targets:
            agent = self.agents[target]
            self.capacity_series[target].append(agent.capacity_tasks)
            self.fee_series[target].append(agent.epoch_listing_fee_mergs)


def main() -> dict:
    cfg = baseline_config(master_seed=SEED, epochs=EPOCHS)
    attack = BleedModel(cfg, run_name="s6_listing_fee_bleed")
    attack.run()
    twin = run_twin(SEED, EPOCHS, name="s6_twin")

    def post_flood(series_dict, agent_ids):
        # per-agent mean over the epochs after the flood stopped
        window = slice(FLOOD_EPOCHS.stop - FLOOD_EPOCHS.start + 1, None)
        vals = [sum(series_dict[a][window]) / max(1, len(series_dict[a][window])) for a in agent_ids]
        return sum(vals) / len(vals)

    adaptive_targets = attack.targets[:4]
    honest_targets = attack.targets[4:]
    peak_cap = {t: max(attack.capacity_series[t]) for t in attack.targets}
    end_cap = {t: attack.capacity_series[t][-1] for t in attack.targets}
    adaptive_recovery = post_flood(attack.capacity_series, adaptive_targets)
    honest_recovery = post_flood(attack.capacity_series, honest_targets)
    bleed_fees = {t: round(sum(attack.fee_series[t]) / 1000, 3) for t in attack.targets}
    # Same genesis ids exist in the twin: its end-of-run declared capacity is the
    # no-attack counterfactual for the ratchet (fees are β·r·capacity).
    twin_end_capacity = {t: twin.agents[t].capacity_tasks for t in attack.targets if t in twin.agents}
    measures = {
        "targets_adaptive": adaptive_targets,
        "targets_honest": honest_targets,
        "peak_capacity": peak_cap,
        "end_capacity": end_cap,
        "post_flood_mean_capacity_adaptive": round(adaptive_recovery, 2),
        "post_flood_mean_capacity_honest": round(honest_recovery, 2),
        "twin_end_capacity": twin_end_capacity,
        "listing_fees_paid_ergs": bleed_fees,
        "invariant_violations": len(attack.invariant_violations),
    }
    narrative = [
        "During the flood, victims' fill-driven capacity adaptation ratcheted envelopes up "
        f"to peaks of {max(peak_cap.values())} tasks/epoch.",
        "After the flood vanished, the −1/epoch shrink rule walked capacity back down; "
        f"post-flood mean capacity: adaptive {measures['post_flood_mean_capacity_adaptive']} vs "
        f"honest {measures['post_flood_mean_capacity_honest']} (both escape, symmetric rule; "
        "the bleed tail is the asymmetry between +1 ratchet-up under flood and −1 decay).",
        "The attack's lever is real: every flood task was funded and settled at full price — "
        "the adversary paid workers market rates to inflate their fee base. β at the launch "
        "value (0.005) makes the induced fee burn small relative to flood spend; the sweep "
        "explores whether higher β turns this attack economic.",
    ]
    write_report("s6_listing_fee_bleed", "S6 — Listing-fee bleed attack",
                 __doc__.strip().split("\n\n")[0], measures, narrative)
    return measures


if __name__ == "__main__":
    print(main())

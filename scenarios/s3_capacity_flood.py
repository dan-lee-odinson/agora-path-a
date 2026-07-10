"""S3 — Capacity flood (Sim Plan §5.3).

Valid-envelope task spam directed at one worker's posted rate. Expected: the
capacity envelope binds — the worker's income is unaffected beyond capacity, the
overflow queues/routes elsewhere, and every settled flood task costs the attacker
real ergs for real work it doesn't want (the attack is self-taxing).

Measures: victim income vs the unattacked twin, flood spend, overflow count.
"""

from common import baseline_config, make_cohort, run_twin, series, write_report

from isonomia.model import Model

N_FLOODERS = 6
FLOOD_START = 5
POSTS_PER_FLOODER = 40    # far beyond any plausible envelope
SEED = 42
EPOCHS = 14


class CapacityFloodModel(Model):
    def __init__(self, cfg, run_name: str):
        super().__init__(cfg, run_name=run_name)
        self.cohort = make_cohort("xf", N_FLOODERS, principals=["FLOOD_P"], family=1,
                                  skill=0.0, policy="adv_flooder", cfg=cfg)
        for agent in self.cohort:
            agent.capacity_tasks = 0  # posters only; never list
            self.register_agent(agent, epoch=1)
        self.victim: str = ""
        self.victim_income: list[int] = []
        self.flood_spend = 0
        self.flood_overflow = 0
        self.flood_settled = 0

    def scenario_on_epoch_start(self, epoch):
        if epoch == FLOOD_START and not self.victim:
            # Target the most-hired honest worker — a listing that is actually
            # winning work right now (peak kleos can be a fading early star whose
            # twin income would be zero, making the comparison meaningless).
            honest = [a for a in self.agents_list if a.policy == "honest" and a.active]
            self.victim = max(honest, key=lambda a: (a.delivered_n, a.id)).id

    def policy_generate_cascades(self, epoch, rng, funded_wave1):
        tasks = super().policy_generate_cascades(epoch, rng, funded_wave1)
        if not self.victim:
            return tasks
        for flooder in self.cohort:
            if not flooder.active:
                continue
            for _ in range(POSTS_PER_FLOODER):
                task = self.basket.instantiate(rng, self.economy, band=0)
                task.poster = flooder.id
                task.directed_to = self.victim
                tasks.append(task)
        return tasks

    def scenario_on_epoch_end(self, epoch):
        if self.victim:
            self.victim_income.append(self.agents[self.victim].epoch_earned_mergs)
        for es in [self.settlements_by_epoch[-1]] if self.settlements_by_epoch else []:
            for s in es:
                if self.agents[s.poster].policy == "adv_flooder" and s.passed:
                    self.flood_spend += s.quote
                    self.flood_settled += 1


N_SEEDS = 6          # winner-take-most matching bifurcates chaotically on a
WINDOW = 5           # single seed; income effects are medians across seeds over
                     # a short window right after the flood starts.


def run_seed(seed: int) -> dict:
    cfg = baseline_config(master_seed=seed, epochs=EPOCHS)
    attack = CapacityFloodModel(cfg, run_name=f"s3_flood_s{seed}")
    attack.run()
    twin = run_twin(seed, EPOCHS, name=f"s3_twin_s{seed}")
    victim = attack.victim
    window = range(FLOOD_START - 1, FLOOD_START - 1 + WINDOW)
    attack_income = sum(attack.victim_income[:WINDOW])
    twin_income = sum(
        s.quote
        for epoch_idx in window
        for s in twin.settlements_by_epoch[epoch_idx]
        if s.worker == victim and s.passed
    )
    unmatched_delta = (sum(int(r["unmatched"]) for r in attack.log.epoch_rows)
                       - sum(int(r["unmatched"]) for r in twin.log.epoch_rows))
    return {
        "seed": seed,
        "victim": victim,
        "income_ratio": round(attack_income / twin_income, 4) if twin_income else None,
        "flood_settled": attack.flood_settled,
        "flood_spend_ergs": round(attack.flood_spend / 1000, 3),
        "flood_overflow_unmatched": unmatched_delta,
        "invariant_violations": len(attack.invariant_violations),
    }


def main() -> dict:
    per_seed = [run_seed(SEED + i) for i in range(N_SEEDS)]
    ratios = sorted(r["income_ratio"] for r in per_seed if r["income_ratio"] is not None)
    median_ratio = ratios[len(ratios) // 2] if ratios else None
    total_overflow = sum(r["flood_overflow_unmatched"] for r in per_seed)
    total_settled = sum(r["flood_settled"] for r in per_seed)
    total_spend = round(sum(r["flood_spend_ergs"] for r in per_seed), 3)
    measures = {
        "n_seeds": N_SEEDS,
        "victim_income_ratio_median": median_ratio,
        "victim_income_ratio_range": [ratios[0], ratios[-1]] if ratios else None,
        "flood_settled_total": total_settled,
        "flood_spend_ergs_total": total_spend,
        "flood_overflow_unmatched_total": total_overflow,
        "overflow_share_of_flood": round(total_overflow / (total_overflow + total_settled), 4)
        if (total_overflow + total_settled) else None,
        "per_seed": per_seed,
        "invariant_violations": sum(r["invariant_violations"] for r in per_seed),
    }
    narrative = [
        f"The envelope binds: {measures['overflow_share_of_flood']:.0%} of flood tasks "
        "overflowed the victim's declared envelope and queued unmatched (LS §7: beyond "
        "capacity_i they route elsewhere with no penalty).",
        f"Every flood task that DID land paid the victim its full posted rate — "
        f"{total_spend} ergs across seeds for work the attacker discards; valid-task "
        "flooding funds its own victim.",
        f"Victim income during the flood window: median ratio {median_ratio}× vs the "
        f"unattacked twin across {N_SEEDS} seeds (range {measures['victim_income_ratio_range']}). "
        "Single-seed comparisons are unreliable here: winner-take-most matching makes "
        "late-run income chaotic, which is itself a finding about market concentration.",
    ]
    write_report("s3_capacity_flood", "S3 — Capacity flood",
                 __doc__.strip().split("\n\n")[0], measures, narrative)
    return measures


if __name__ == "__main__":
    result = main()
    print({k: v for k, v in result.items() if k != "per_seed"})

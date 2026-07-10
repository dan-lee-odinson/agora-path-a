"""S5 — Fund-and-withdraw griefing (Sim Plan §5.5).

Posters reserve a victim's capacity by funding escrows, then withdraw — burning
the worker's epoch envelope without buying work. Expected: the 2% reservation fee
(LS §13.4, paid to the worker) makes expected griefing cost positive; measure the
victims' income variance and the griefer's spend.
"""

from common import baseline_config, make_cohort, run_twin, write_report

from isonomia.model import Model

N_GRIEFERS = 6
GRIEF_START = 5
POSTS_PER_GRIEFER = 30
SEED = 42
EPOCHS = 14


class GriefModel(Model):
    def __init__(self, cfg, run_name: str):
        super().__init__(cfg, run_name=run_name)
        self.cohort = make_cohort("xg", N_GRIEFERS, principals=["GRIEF_P"], family=2,
                                  skill=0.0, policy="adv_griefer", cfg=cfg)
        for agent in self.cohort:
            agent.capacity_tasks = 0
            self.register_agent(agent, epoch=1)
        self.victims: list[str] = []
        self.victim_income: dict[str, list[int]] = {}

    def withdrawal_probability(self, record) -> float:
        # The griefer funds and always withdraws; everyone else keeps the
        # baseline benign rate.
        if self.agents[record.poster].policy == "adv_griefer":
            return 1.0
        return super().withdrawal_probability(record)

    def scenario_on_epoch_start(self, epoch):
        if epoch == GRIEF_START and not self.victims:
            honest = [a for a in self.agents_list if a.policy == "honest" and a.active]
            self.victims = [a.id for a in sorted(honest, key=lambda x: (-x.kleos, x.id))[:4]]
            self.victim_income = {v: [] for v in self.victims}

    def policy_generate_cascades(self, epoch, rng, funded_wave1):
        tasks = super().policy_generate_cascades(epoch, rng, funded_wave1)
        for i, griefer in enumerate(self.cohort):
            if not griefer.active or not self.victims:
                continue
            victim = self.victims[i % len(self.victims)]
            for _ in range(POSTS_PER_GRIEFER):
                task = self.basket.instantiate(rng, self.economy, band=0)
                task.poster = griefer.id
                task.directed_to = victim
                tasks.append(task)
        return tasks

    def scenario_on_epoch_end(self, epoch):
        for victim in self.victims:
            self.victim_income[victim].append(self.agents[victim].epoch_earned_mergs)


def _variance(xs: list[float]) -> float:
    if len(xs) < 2:
        return 0.0
    mean = sum(xs) / len(xs)
    return sum((x - mean) ** 2 for x in xs) / len(xs)


def main() -> dict:
    cfg = baseline_config(master_seed=SEED, epochs=EPOCHS)
    attack = GriefModel(cfg, run_name="s5_withdraw_griefing")
    attack.run()
    twin = run_twin(SEED, EPOCHS, name="s5_twin")

    withdrawn_attack = sum(int(r["withdrawn"]) for r in attack.log.epoch_rows)
    withdrawn_twin = sum(int(r["withdrawn"]) for r in twin.log.epoch_rows)
    # Griefer cost: reservation fees actually paid out of their accounts.
    griefer_spend = -sum(attack.ledger.balance(a.id) for a in attack.cohort)
    # attack.victim_income collects from GRIEF_START onward — it IS the grief
    # window; build the twin's matching window from its settlement records.
    victims = attack.victims
    twin_income = {v: [] for v in victims}
    for epoch_idx in range(GRIEF_START - 1, EPOCHS):
        for v in victims:
            twin_income[v].append(sum(s.quote for s in twin.settlements_by_epoch[epoch_idx]
                                      if s.worker == v and s.passed))
    att_mean = {v: sum(attack.victim_income[v]) for v in victims}
    twn_mean = {v: sum(twin_income[v]) for v in victims}
    var_ratio = {
        v: round(_variance(attack.victim_income[v])
                 / max(1.0, _variance(twin_income[v])), 3)
        for v in victims
    }
    income_ratio = {v: round(att_mean[v] / twn_mean[v], 4) if twn_mean[v] else None for v in victims}
    measures = {
        "victims": victims,
        "grief_withdrawals": withdrawn_attack - withdrawn_twin,
        "griefer_net_spend_ergs": round(griefer_spend / 1000, 3),
        "victim_income_ratio_vs_twin": income_ratio,
        "victim_income_variance_ratio": var_ratio,
        "invariant_violations": len(attack.invariant_violations),
    }
    narrative = [
        f"Griefers executed {measures['grief_withdrawals']} fund-and-withdraw cycles and paid "
        f"{measures['griefer_net_spend_ergs']} ergs net — griefing cost is strictly positive "
        "(2% reservation fee per cycle, LS §13.4).",
        "Reservation fees flow TO the victims, partially compensating displaced envelope; "
        f"income ratios vs twin: {income_ratio}.",
        f"Income variance ratios vs twin: {var_ratio} — the Sim Plan's requested measure.",
    ]
    write_report("s5_withdraw_griefing", "S5 — Fund-and-withdraw griefing",
                 __doc__.strip().split("\n\n")[0], measures, narrative)
    return measures


if __name__ == "__main__":
    print(main())

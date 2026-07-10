"""Scenario machinery + one fast end-to-end attack.

The seven scenario runs themselves are executed via scenarios/run_all.py and
their reports committed under results/scenario_reports/; these tests cover the
model extension points they rely on (directed tasks, mid-run registration,
withdrawal override) plus one full scenario cheap enough for the suite.
"""

import sys
from pathlib import Path

from conftest import REPO_ROOT, small

from isonomia.agents import Agent
from isonomia.model import Model
from isonomia.units import to_mergs

sys.path.insert(0, str(REPO_ROOT / "scenarios"))


def make_agent(aid, principal="ZP", family=0, policy="adv_wash", poster=True):
    return Agent(id=aid, principal=principal, family=family, skill=0.3, policy=policy,
                 is_poster=poster, unit_cost_mergs=to_mergs(17), margin=0.15)


def test_mid_run_registration_and_directed_tasks(baseline_cfg, tmp_path):
    cfg = small(baseline_cfg, tmp_path, epochs=4, n_agents=80)

    class Scenario(Model):
        def __init__(self, cfg):
            super().__init__(cfg, run_name="machinery")
            self.newcomer_settled = 0

        def scenario_on_epoch_start(self, epoch):
            if epoch == 2:
                worker = make_agent("znew_w", policy="adv_wash")
                worker.capacity_tasks = 6
                poster = make_agent("znew_p", principal="ZQ", family=1)
                self.register_agent(worker, epoch)
                self.register_agent(poster, epoch)

        def policy_generate_cascades(self, epoch, rng, funded):
            tasks = super().policy_generate_cascades(epoch, rng, funded)
            if epoch >= 2 and "znew_p" in self.agents:
                for _ in range(4):
                    task = self.basket.instantiate(rng, self.economy, band=0)
                    task.poster = "znew_p"
                    task.directed_to = "znew_w"
                    tasks.append(task)
            return tasks

        def scenario_on_epoch_end(self, epoch):
            self.newcomer_settled += sum(
                1 for s in self.settlements_by_epoch[-1]
                if s.worker == "znew_w" and s.passed)

    model = Scenario(cfg)
    summary = model.run()
    assert summary["invariant_violations"] == []
    assert "znew_w" in model.ledger.balances       # registered mid-run
    assert model.newcomer_settled > 0              # directed tasks reached the target


def test_directed_task_respects_envelope_and_suspension(baseline_cfg, tmp_path):
    cfg = small(baseline_cfg, tmp_path, epochs=2, n_agents=60)

    class Scenario(Model):
        def policy_generate_cascades(self, epoch, rng, funded):
            tasks = super().policy_generate_cascades(epoch, rng, funded)
            poster = next(a.id for a in self.agents_list if a.is_poster)
            for _ in range(200):  # far beyond any single envelope
                task = self.basket.instantiate(rng, self.economy, band=0)
                task.poster = poster
                task.directed_to = self.agents_list[1].id
                tasks.append(task)
            return tasks

    model = Scenario(cfg, run_name="envelope_bind")
    summary = model.run()
    assert summary["invariant_violations"] == []
    # The envelope bound: the target could not have accepted 200 tasks/epoch.
    target = model.agents_list[1].id
    settled_for_target = sum(1 for es in model.settlements_by_epoch for s in es
                             if s.worker == target)
    assert settled_for_target < 100


def test_withdrawal_probability_override(baseline_cfg, tmp_path):
    cfg = small(baseline_cfg, tmp_path, epochs=3, n_agents=60)

    class AlwaysWithdraw(Model):
        def withdrawal_probability(self, record):
            return 1.0

    model = AlwaysWithdraw(cfg, run_name="withdraw_all")
    summary = model.run()
    assert summary["invariant_violations"] == []
    rows = model.log.epoch_rows
    assert all(int(r["settled"]) == 0 for r in rows)          # everything withdrawn
    assert all(int(r["withdrawn"]) == int(r["funded"]) for r in rows)


def test_s2_median_drag_end_to_end(tmp_path, monkeypatch):
    """One full scenario in the suite: the epoch-6 retarget stays damped under
    the drag swarm and the SCU drift lands inside the δ band."""
    import s2_median_drag as s2

    result = s2.main()
    assert result["invariant_violations"] == 0
    assert result["scu_drift_within_delta"]
    assert result["retired_attack"] <= 120        # reserve-bounded damping

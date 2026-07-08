"""Registry: activation-qualification rules (LS §9) — the quality bar demands
same-principal and same-lineage exclusion — plus caps, origin diversity, kleos."""

from agora.agents import Agent
from agora.records import SettlementRecord
from agora.registry import Registry
from test_ledger import make_params

ACT_CFG = {
    "min_agents": 150, "min_qualified_settlements": 5000,
    "fee_convergence_epochs": 3, "fee_convergence_band": 0.20,
    "min_principals": 40, "principal_share_cap": 0.15,
    "pair_share_cap": 0.02, "min_origin_principals": 25,
}


def make_registry():
    return Registry(make_params(), ACT_CFG)


def settlement(poster_p="P1", worker_p="P2", poster_f=0, worker_f=1,
               passed=True, washed=False, eid=0):
    return SettlementRecord(
        escrow_id=eid, epoch=1, poster="aP", worker="aW",
        poster_principal=poster_p, worker_principal=worker_p,
        poster_family=poster_f, worker_family=worker_f,
        template_id=0, band=0, size_units=1.0, quote=20_000,
        passed=passed, disputed=False, seeded_fault=False, wash_flagged=washed,
    )


def test_same_principal_trades_are_unqualified():
    registry = make_registry()
    assert not registry.qualifies(settlement(poster_p="P1", worker_p="P1"))


def test_same_lineage_trades_are_unqualified():
    registry = make_registry()
    assert not registry.qualifies(settlement(poster_f=2, worker_f=2))  # DECISIONS #6


def test_wash_flagged_and_failed_are_unqualified():
    registry = make_registry()
    assert not registry.qualifies(settlement(washed=True))
    assert not registry.qualifies(settlement(passed=False))
    assert registry.qualifies(settlement())  # the clean cross-principal cross-family trade


def test_pair_caps_bound_concentration():
    registry = make_registry()
    # 300 clean settlements spread over 300 distinct principal pairs + 400 hammered
    # through one pair.
    records = []
    for i in range(300):
        records.append(settlement(poster_p=f"P{i:03d}", worker_p=f"Q{i:03d}",
                                  poster_f=0, worker_f=1, eid=i))
    for i in range(400):
        records.append(settlement(poster_p="PX", worker_p="QX",
                                  poster_f=0, worker_f=1, eid=1000 + i))
    registry.process_settlements(records)
    assert registry.candidate_total == 700
    capped = registry.qualified_capped()
    # The hot pair may contribute at most 2% of the capped total (LS §9); the
    # concentrated 400 collapse to noise instead of advancing the clock.
    hot_contribution = capped - 300
    assert 0 <= hot_contribution <= max(1, int(0.02 * capped))
    assert 300 <= capped <= 310


def test_principal_caps_bound_fan_out_concentration():
    registry = make_registry()
    # One principal fans out over 100 counterparties (evading the pair cap) with 6
    # settlements each; 400 dispersed cleans elsewhere.
    records = []
    eid = 0
    for i in range(100):
        for _ in range(6):
            records.append(settlement(poster_p="PX", worker_p=f"Q{i:03d}",
                                      poster_f=0, worker_f=1, eid=eid))
            eid += 1
    for i in range(400):
        records.append(settlement(poster_p=f"R{i:03d}", worker_p=f"S{i:03d}",
                                  poster_f=0, worker_f=1, eid=10_000 + i))
    registry.process_settlements(records)
    assert registry.candidate_total == 1000
    capped = registry.qualified_capped()
    # PX may participate in at most 15% of the capped total: 400 dispersed +
    # PX's allowed ≈ 0.15·Q ⇒ Q ≈ 400/0.85 ≈ 470.
    assert 455 <= capped <= 485


def test_origin_diversity_tracks_posting_principals():
    registry = make_registry()
    records = [settlement(poster_p=f"P{i:02d}", worker_p="W", eid=i) for i in range(30)]
    registry.process_settlements(records)
    assert len(registry.origin_principals) == 30


def test_activation_requires_all_gates():
    registry = make_registry()
    for i in range(200):
        agent = Agent(id=f"a{i:04d}", principal=f"P{i % 50:03d}", family=i % 4, skill=0.0,
                      policy="honest", is_poster=True, unit_cost_mergs=17_000, margin=0.15)
        registry.register(agent)
    # Enough clean qualified settlements, spread over 100 distinct pairs so the
    # 2% pair cap has headroom (a <50-pair economy is degenerate under a 2% cap
    # by construction).
    records = []
    eid = 0
    for round_ in range(60):
        for i in range(100):
            records.append(settlement(poster_p=f"P{i:03d}", worker_p=f"Q{i:03d}",
                                      poster_f=0, worker_f=1, eid=eid))
            eid += 1
    registry.process_settlements(records)
    status = registry.activation_status(epoch=10, fee_convergence_streak=3)
    assert status["agents_ok"] and status["principals_ok"] and status["origin_ok"]
    assert status["settlements_ok"] and status["fee_ok"] and status["activated"]
    assert registry.activation_epoch == 10
    # Missing fee convergence blocks activation on its own.
    registry2 = make_registry()
    for agent in registry.agents.values():
        registry2.register(agent)
    registry2.process_settlements(records)
    status2 = registry2.activation_status(epoch=10, fee_convergence_streak=2)
    assert not status2["activated"]


def test_kleos_awards_and_decay():
    registry = make_registry()
    agent = Agent(id="a0001", principal="P1", family=0, skill=0.0, policy="honest",
                  is_poster=False, unit_cost_mergs=17_000, margin=0.15)
    registry.register(agent)
    registry.award_kleos("a0001", 2.5)
    registry.decay_kleos()
    assert abs(agent.kleos - 2.5 * make_params().kleos_epoch_decay) < 1e-12


def test_governance_weight_cap_binds():
    registry = make_registry()
    for i, kleos in enumerate([1000.0, 10.0, 10.0, 10.0]):
        agent = Agent(id=f"a{i:04d}", principal="P1", family=0, skill=0.0, policy="honest",
                      is_poster=False, unit_cost_mergs=17_000, margin=0.15)
        agent.kleos = kleos
        registry.register(agent)
    report = registry.governance_report(w_cap_frac=0.02)
    cap = 0.02 * 1030.0
    assert report["weights"]["a0000"] == cap    # WP §10.5: the whale is capped
    assert report["weights"]["a0001"] == 10.0

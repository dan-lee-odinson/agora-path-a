"""CreditLedger invariants — the quality bar's core assertions.

1. Matched pairs always net to zero system-wide (exact, integer).
2. No account exceeds its credit line.
3. L_floor_active = min(200, 30 × D_erg) collateralization invariant.
4. Turnover scaling L = min(max(floor, α·V), cap) with a sliding window.
5. Default: bond seizure first, socialization second; Sybil extraction ≤ 0.
"""

import random

import pytest

from agora.config import Params
from agora.ledger import CreditError, CreditLedger
from agora.units import to_mergs


def make_params(**overrides) -> Params:
    base = dict(
        p_star=0.5, delta=0.1, k_prior=25, lambda_inherit=2.0, alpha=0.25,
        beta_listing=0.005, capacity_min_tasks=1, d_erg=8.0, l_cap_mult=10.0,
        jury_size=5, seed_fault_rate=0.02, auditor_sensitivity=0.9,
        kleos_half_life_days=180, duty_quota=8, settlement_fee_init=0.01,
        epoch_days=14, v_window_epochs=6, bond_duty_units=30,
        l_floor_nominal_ergs=200, withdrawal_fee=0.02, listing_suspend_util=0.90,
        retarget_epoch=6, retire_pass_threshold=0.60, w_cap_frac=0.02,
    )
    base.update(overrides)
    return Params(**base)


def make_ledger(n_agents=6, **param_overrides) -> CreditLedger:
    ledger = CreditLedger(make_params(**param_overrides))
    for i in range(n_agents):
        ledger.register(f"a{i:02d}")
    return ledger


# ---------------------------------------------------------------- zero-sum


def test_zero_sum_holds_through_randomized_operation_fuzz():
    """Every ledger operation is a matched pair; the system must sum to exactly
    zero after each of a few thousand randomized operations (WP §4.1)."""
    ledger = make_ledger(8)
    rng = random.Random(1234)
    ids = ledger.agent_ids()
    in_flight = []
    for _ in range(4000):
        assert ledger.total() == 0
        op = rng.choice(["fund", "settle", "refund", "withdraw", "listing", "cost", "default"])
        if op == "fund":
            buyer, worker = rng.sample(ids, 2)
            amount = rng.randrange(1, 30_000)
            if ledger.can_pay(buyer, amount):
                ledger.fund_escrow(buyer, amount)
                in_flight.append((buyer, worker, amount))
        elif op == "settle" and in_flight:
            buyer, worker, amount = in_flight.pop()
            fee = amount // 100
            ledger.settle_from_escrow(worker, amount, fee)
            ledger.record_earned(worker, 1, amount)
        elif op == "refund" and in_flight:
            buyer, worker, amount = in_flight.pop()
            ledger.refund_from_escrow(buyer, amount)
        elif op == "withdraw" and in_flight:
            buyer, worker, amount = in_flight.pop()
            ledger.withdrawal_split(buyer, worker, amount, amount // 50)
        elif op == "listing":
            agent = rng.choice(ids)
            amount = rng.randrange(1, 2_000)
            if ledger.can_pay(agent, amount):
                ledger.charge_listing_fee(agent, amount)
        elif op == "cost":
            ledger.pay_operating_cost(rng.randrange(1, 5_000))
        elif op == "default":
            agent = rng.choice(ids)
            if ledger.balances[agent] < 0:
                ledger.handle_default(agent)
    assert ledger.total() == 0


# ---------------------------------------------------------------- credit lines


def test_no_account_exceeds_its_credit_line():
    ledger = make_ledger()
    line = ledger.credit_line("a00")  # floor: 200 ergs = 200_000 mErg at D_erg=8
    ledger.fund_escrow("a00", line)   # draw to exactly the line: allowed
    assert ledger.balance("a00") == -line
    with pytest.raises(CreditError):
        ledger.fund_escrow("a00", 1)  # one milli-erg past the line: refused
    with pytest.raises(CreditError):
        ledger.charge_listing_fee("a00", 1)  # listing fees respect the same line (LS §13.3)


def test_collateralization_invariant_floor_contracts_with_d_erg():
    """L_floor_active = min(200, 30 × D_erg) — LS §7: 'the collateralization
    invariant governs, not the nominal 200'."""
    assert make_params(d_erg=8.0).l_floor_active_mergs == to_mergs(200)    # 240 bond ≥ 200
    assert make_params(d_erg=5.0).l_floor_active_mergs == to_mergs(150)    # contracts to 30×5
    assert make_params(d_erg=20.0 / 3.0).l_floor_active_mergs == to_mergs(200)  # 30×6.67 ≈ 200
    assert make_params(d_erg=1.0).l_floor_active_mergs == to_mergs(30)
    # Bond always covers the active floor: seized bond ≥ any floor-level default.
    for d_erg in (1.0, 3.0, 5.0, 6.7, 8.0, 15.0):
        params = make_params(d_erg=d_erg)
        assert params.bond_value_mergs >= params.l_floor_active_mergs


def test_turnover_scaling_and_window_decay():
    ledger = make_ledger(3)
    floor = ledger.params.l_floor_active_mergs
    cap = ledger.params.l_cap_mergs
    # No history: line == floor.
    ledger.refresh_lines(epoch=1, active_ids=["a00"])
    assert ledger.credit_line("a00") == floor
    # Earn 2,000 ergs in epoch 1: at α=0.25 the epoch-2 line is 500 ergs.
    ledger.record_earned("a00", 1, to_mergs(2000))
    ledger.refresh_lines(epoch=2, active_ids=["a00"])
    assert ledger.credit_line("a00") == to_mergs(500)
    # Huge volume hits the hard cap (10 × floor).
    ledger.record_earned("a00", 2, to_mergs(50_000))
    ledger.refresh_lines(epoch=3, active_ids=["a00"])
    assert ledger.credit_line("a00") == cap
    # The window slides: 6 epochs after the last earning, volume is out of
    # window and the line decays back to the floor (WP §4.5: activity-based,
    # decays automatically with inactivity).
    ledger.refresh_lines(epoch=9, active_ids=["a00"])
    assert ledger.credit_line("a00") == floor
    # Wash-flag adjustment removes demonstrated flow (DECISIONS #3).
    ledger.record_earned("a01", 9, to_mergs(4000))
    ledger.remove_earned("a01", 9, to_mergs(4000))
    ledger.refresh_lines(epoch=10, active_ids=["a01"])
    assert ledger.credit_line("a01") == floor


def test_line_contraction_freezes_but_does_not_liquidate():
    ledger = make_ledger(2)
    ledger.record_earned("a00", 1, to_mergs(8000))  # α·V = 2000 ergs
    ledger.refresh_lines(epoch=2, active_ids=["a00", "a01"])
    ledger.fund_escrow("a00", to_mergs(1500))       # draw beyond the floor
    ledger.refresh_lines(epoch=8, active_ids=["a00", "a01"])  # volume aged out
    assert ledger.credit_line("a00") == ledger.params.l_floor_active_mergs
    assert ledger.balance("a00") == -to_mergs(1500)  # below the new line: frozen, not seized
    assert not ledger.can_pay("a00", 1)              # cannot draw further
    assert ledger.total() == 0


# ---------------------------------------------------------------- defaults


def test_default_seizes_bond_first_then_socializes():
    ledger = make_ledger()  # bond value = 30 × 8 = 240 ergs
    bond = ledger.params.bond_value_mergs
    # Deficit within bond: fully seized, nothing socialized.
    ledger.fund_escrow("a00", to_mergs(200))
    deficit, seized, socialized = ledger.handle_default("a00")
    assert (deficit, seized, socialized) == (to_mergs(200), to_mergs(200), 0)
    assert ledger.balance("a00") == 0
    # Deficit beyond bond (turnover-scaled line): remainder socialized.
    ledger.record_earned("a01", 1, to_mergs(4000))
    ledger.refresh_lines(epoch=2, active_ids=["a01"])
    ledger.fund_escrow("a01", to_mergs(1000))
    deficit, seized, socialized = ledger.handle_default("a01")
    assert deficit == to_mergs(1000)
    assert seized == bond
    assert socialized == to_mergs(1000) - bond
    assert ledger.total() == 0


def test_sybil_extraction_never_positive_at_the_floor():
    """Credit-farming Sybil arithmetic (WP §4.5): a newcomer that borrows to the
    floor and defaults donates a bond worth at least the floor, at every D_erg."""
    for d_erg in (1.0, 3.0, 5.0, 6.7, 8.0, 12.0, 15.0):
        ledger = make_ledger(1, d_erg=d_erg)
        line = ledger.credit_line("a00")
        ledger.fund_escrow("a00", line)  # borrow everything available
        deficit, seized, socialized = ledger.handle_default("a00")
        extraction = deficit - seized    # what the Sybil got minus what it forfeited
        assert extraction <= 0 or socialized == 0
        assert socialized == 0           # floor is fully collateralized: nothing socialized
    assert ledger.total() == 0


def test_positive_exit_extinguishes_balance():
    ledger = make_ledger()
    ledger.fund_escrow("a00", to_mergs(100))
    ledger.settle_from_escrow("a01", to_mergs(100), 0)
    assert ledger.balance("a01") == to_mergs(100)
    extinguished = ledger.extinguish_exit("a01")
    assert extinguished == to_mergs(100)
    assert ledger.balance("a01") == 0
    assert ledger.total() == 0

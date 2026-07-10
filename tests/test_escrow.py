"""Escrow lifecycle invariants (Launch Spec §13.4):

capacity consumed at FUNDING; released/restored on every defined event; the 2%
withdrawal reservation fee goes to the worker; the buyer's total debit is exactly
the escrowed quote (LS §13.1).
"""

import pytest

from isonomia.escrow import Escrow
from isonomia.units import fee_of, to_mergs
from test_ledger import make_ledger


class CapacityStub:
    """Counts consume/restore calls so tests can assert *when* capacity moves."""

    def __init__(self):
        self.consumed: dict[str, int] = {}
        self.restored: dict[str, int] = {}

    def consume(self, worker, mergs):
        self.consumed[worker] = self.consumed.get(worker, 0) + mergs
        return True

    def restore(self, worker, mergs):
        self.restored[worker] = self.restored.get(worker, 0) + mergs

    def net(self, worker):
        return self.consumed.get(worker, 0) - self.restored.get(worker, 0)


def setup():
    ledger = make_ledger(4)
    escrow = Escrow(ledger, ledger.params)
    return ledger, escrow, CapacityStub()


def test_capacity_consumed_at_funding_not_at_posting():
    ledger, escrow, cap = setup()
    # "Posting" has no ledger/capacity API at all — only fund() touches either.
    assert cap.consumed == {}
    record = escrow.fund("a00", "a01", to_mergs(20), band=0, epoch=1, capacity=cap)
    assert record is not None
    assert cap.consumed == {"a01": to_mergs(20)}
    assert ledger.balance("a00") == -to_mergs(20)   # credit drawn at funding
    assert ledger.balance("ESCROW") == to_mergs(20)


def test_funding_failure_consumes_nothing():
    ledger, escrow, cap = setup()
    line = ledger.credit_line("a00")
    record = escrow.fund("a00", "a01", line + 1, band=0, epoch=1, capacity=cap)
    assert record is None
    assert escrow.epoch_counters["funding_failures"] == 1
    assert cap.consumed == {}                        # nothing consumed (LS §13.4)
    assert ledger.balance("a00") == 0
    assert ledger.total() == 0


def test_settlement_pays_quote_minus_fee_and_keeps_envelope_consumed():
    ledger, escrow, cap = setup()
    quote = to_mergs(20)
    record = escrow.fund("a00", "a01", quote, band=0, epoch=1, capacity=cap)
    fee = escrow.settle(record, passed=True, fee_rate=0.01)
    assert fee == fee_of(quote, 0.01)
    assert ledger.balance("a01") == quote - fee      # worker-side fee (DECISIONS #4)
    assert ledger.balance("FEEPOOL") == fee
    assert ledger.balance("a00") == -quote           # buyer paid exactly the quote (LS §13.1)
    assert ledger.balance("ESCROW") == 0
    assert cap.net("a01") == quote                   # slot occupied: envelope stays consumed
    assert ledger.earned["a01"][1] == quote          # demonstrated flow recorded
    assert ledger.total() == 0


def test_failed_verification_refunds_in_full_no_fee():
    ledger, escrow, cap = setup()
    quote = to_mergs(30)
    record = escrow.fund("a00", "a01", quote, band=0, epoch=1, capacity=cap)
    fee = escrow.settle(record, passed=False, fee_rate=0.01)
    assert fee == 0
    assert ledger.balance("a00") == 0                # full refund (DECISIONS #8)
    assert ledger.balance("a01") == 0
    assert ledger.balance("FEEPOOL") == 0
    assert cap.net("a01") == quote                   # slot was occupied: stays consumed
    assert ledger.total() == 0


def test_withdrawal_pays_2pct_reservation_fee_to_worker_and_restores_envelope():
    ledger, escrow, cap = setup()
    quote = to_mergs(50)
    record = escrow.fund("a00", "a01", quote, band=0, epoch=1, capacity=cap)
    fee = escrow.withdraw(record, capacity=cap)
    assert fee == fee_of(quote, 0.02)                # 2% (LS §13.4)
    assert ledger.balance("a01") == fee              # ...to the WORKER
    assert ledger.balance("a00") == -fee             # poster bore exactly the fee
    assert cap.net("a01") == 0                       # envelope restored (DECISIONS #19)
    assert ledger.total() == 0


def test_invalidation_refunds_in_full_and_restores_envelope():
    ledger, escrow, cap = setup()
    quote = to_mergs(25)
    record = escrow.fund("a00", "a01", quote, band=0, epoch=1, capacity=cap)
    escrow.invalidate(record, capacity=cap)
    assert ledger.balance("a00") == 0
    assert ledger.balance("a01") == 0
    assert cap.net("a01") == 0
    assert ledger.total() == 0


def test_no_double_resolution():
    ledger, escrow, cap = setup()
    record = escrow.fund("a00", "a01", to_mergs(20), band=0, epoch=1, capacity=cap)
    escrow.settle(record, passed=True, fee_rate=0.01)
    with pytest.raises(ValueError):
        escrow.settle(record, passed=True, fee_rate=0.01)
    with pytest.raises(ValueError):
        escrow.withdraw(record, capacity=cap)

"""Escrow — task funding and verification-conditioned release (Launch Spec §6, §13.4).

The §13.4 lifecycle rules, exactly:
  * capacity is consumed at ESCROW FUNDING — not at posting, not at settlement;
  * unfunded posts consume nothing;
  * reserved capacity releases on: settlement, poster withdrawal, task invalidation
    (envelope violation), or funding failure;
  * poster withdrawal after funding pays a reservation fee (2% of quote) TO THE WORKER.

Envelope accounting nuance (DECISIONS #19): the acceptance obligation is per-epoch
("the maximum erg-volume ... obligated to accept per epoch", LS §7), so settlement and
failed verification — cases where the worker's epoch slot was genuinely occupied — leave
the epoch envelope consumed, while withdrawal and invalidation restore it (the work never
happened; the slot can be resold within the epoch). Funding failure never consumed it.

The capacity provider is any object with:
  consume(worker_id, mergs) -> bool     called at funding
  restore(worker_id, mergs) -> None     called on withdrawal / invalidation
(ListingMarket implements this from milestone 3; tests use a stub.)
"""

from __future__ import annotations

import dataclasses

from isonomia.config import Params
from isonomia.ledger import CreditLedger
from isonomia.units import fee_of

FUNDED = "FUNDED"
SETTLED = "SETTLED"
FAILED = "FAILED_VERIFICATION"
WITHDRAWN = "WITHDRAWN"
INVALIDATED = "INVALIDATED"


@dataclasses.dataclass
class EscrowRecord:
    id: int
    poster: str
    worker: str
    quote: int          # mErg; settlement transfers exactly this (LS §13.1)
    band: int
    epoch: int
    status: str = FUNDED


class Escrow:
    def __init__(self, ledger: CreditLedger, params: Params):
        self.ledger = ledger
        self.params = params
        self.records: list[EscrowRecord] = []
        self.epoch_counters: dict[str, int] = {}
        self.reset_epoch_counters()

    def reset_epoch_counters(self) -> None:
        self.epoch_counters = {
            "funded": 0,
            "funding_failures": 0,
            "settled": 0,
            "failed_verification": 0,
            "withdrawn": 0,
            "invalidated": 0,
            "settled_volume": 0,
            "fees": 0,
            "withdrawal_fees": 0,
        }

    # ------------------------------------------------------------------ fund

    def fund(self, poster: str, worker: str, quote: int, band: int, epoch: int, capacity) -> EscrowRecord | None:
        """Fund a matched task. Returns None on funding failure (credit line short) —
        in which case nothing was consumed anywhere (LS §13.4)."""
        if not self.ledger.can_pay(poster, quote):
            self.epoch_counters["funding_failures"] += 1
            return None
        if not capacity.consume(worker, quote):
            # Matching checks headroom first; hitting this means a race the sim
            # does not have. Kept as a hard error so a future bug cannot silently
            # overbook a worker's envelope.
            raise RuntimeError("capacity consume failed after headroom check")
        self.ledger.fund_escrow(poster, quote)
        record = EscrowRecord(id=len(self.records), poster=poster, worker=worker,
                              quote=quote, band=band, epoch=epoch)
        self.records.append(record)
        self.epoch_counters["funded"] += 1
        return record

    # ------------------------------------------------------------------ resolve

    def settle(self, record: EscrowRecord, passed: bool, fee_rate: float) -> int:
        """Resolve delivery. Pass: matched-pair settlement of exactly the quote,
        fee from worker proceeds (DECISIONS #4); returns the fee. Fail: full refund
        to the poster (DECISIONS #8); returns 0. Epoch envelope stays consumed in
        both cases — the worker's slot was occupied."""
        self._require(record, FUNDED)
        if passed:
            fee = fee_of(record.quote, fee_rate)
            self.ledger.settle_from_escrow(record.worker, record.quote, fee)
            self.ledger.record_earned(record.worker, record.epoch, record.quote)
            record.status = SETTLED
            self.epoch_counters["settled"] += 1
            self.epoch_counters["settled_volume"] += record.quote
            self.epoch_counters["fees"] += fee
            return fee
        self.ledger.refund_from_escrow(record.poster, record.quote)
        record.status = FAILED
        self.epoch_counters["failed_verification"] += 1
        return 0

    def withdraw(self, record: EscrowRecord, capacity) -> int:
        """Poster withdrawal after funding: 2% reservation fee to the worker
        (LS §13.4), remainder refunded, epoch envelope restored. Returns the fee."""
        self._require(record, FUNDED)
        fee = fee_of(record.quote, self.params.withdrawal_fee)
        self.ledger.withdrawal_split(record.poster, record.worker, record.quote, fee)
        capacity.restore(record.worker, record.quote)
        record.status = WITHDRAWN
        self.epoch_counters["withdrawn"] += 1
        self.epoch_counters["withdrawal_fees"] += fee
        return fee

    def invalidate(self, record: EscrowRecord, capacity) -> None:
        """Envelope-violating task discovered after funding: full refund, envelope
        restored, no fee (poster-side defect; LS §2.1, §13.4)."""
        self._require(record, FUNDED)
        self.ledger.refund_from_escrow(record.poster, record.quote)
        capacity.restore(record.worker, record.quote)
        record.status = INVALIDATED
        self.epoch_counters["invalidated"] += 1

    @staticmethod
    def _require(record: EscrowRecord, status: str) -> None:
        if record.status != status:
            raise ValueError(f"escrow {record.id} is {record.status}, expected {status}")

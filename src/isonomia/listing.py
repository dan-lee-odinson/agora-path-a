"""ListingMarket — Harberger self-assessment with capacity envelopes (WP §9.1, LS §7).

Every listed worker posts a self-assessed rate r_i (mErg per median-task unit) and a
capacity envelope, and must accept conforming tasks at that rate up to the envelope.
The costly-signal fee β × r_i × capacity_i is charged every epoch: overstatement bleeds
fees, understatement floods the agent with underpriced work — honesty is the equilibrium
the simulation exists to test.

Units per DECISIONS #5: capacity is declared as a task count n_i; the per-epoch
acceptance envelope is the erg-volume r_i × n_i; the listing fee is β · r_i · n_i.

LS §13.3: listing fees may draw against the credit line (listing is a credit-risk
event, no carve-out), and listing in a band is suspended — capacity zero, no penalty —
whenever the account sits within 10% of its credit limit, so an agent cannot list
itself into default.

This class implements the Escrow module's capacity protocol: `consume` at funding,
`restore` on withdrawal/invalidation (DECISIONS #19).
"""

from __future__ import annotations

import dataclasses

from isonomia.config import Params
from isonomia.ledger import CreditLedger
from isonomia.units import fee_of


@dataclasses.dataclass
class Listing:
    worker: str
    rate: int              # mErg per median-task unit (Harberger self-assessment)
    capacity_tasks: int    # declared envelope, tasks/epoch (DECISIONS #5)
    suspended: bool = False
    consumed: int = 0      # mErg of envelope consumed this epoch (at escrow funding)

    @property
    def envelope(self) -> int:
        return self.rate * self.capacity_tasks


class ListingMarket:
    def __init__(self, ledger: CreditLedger, params: Params):
        self.ledger = ledger
        self.params = params
        self.listings: dict[str, Listing] = {}
        self.epoch_listing_revenue = 0
        self.epoch_suspensions = 0
        self.epoch_fees_by_worker: dict[str, int] = {}

    # ------------------------------------------------------------------ declare

    def set_listing(self, worker: str, rate: int, capacity_tasks: int) -> None:
        """Post or update a listing. Capacity below capacity_min delists — a price
        signal without an acceptance obligation defeats the mechanism (LS §7)."""
        if rate <= 0 or capacity_tasks < self.params.capacity_min_tasks:
            self.listings.pop(worker, None)
            return
        self.listings[worker] = Listing(worker=worker, rate=int(rate), capacity_tasks=int(capacity_tasks))

    def delist(self, worker: str) -> None:
        self.listings.pop(worker, None)

    def get(self, worker: str) -> Listing | None:
        return self.listings.get(worker)

    # ------------------------------------------------------------------ epoch open

    def open_epoch(self) -> int:
        """Reset envelopes, apply the LS §13.3 suspension guard, charge β fees.
        Returns this epoch's listing revenue (offsets the next settlement-fee
        retarget per LS §13.2)."""
        self.epoch_listing_revenue = 0
        self.epoch_suspensions = 0
        self.epoch_fees_by_worker = {}
        for worker in sorted(self.listings):
            listing = self.listings[worker]
            listing.consumed = 0
            fee = fee_of(listing.envelope, self.params.beta_listing)
            # Suspension guard: within 10% of the credit limit, or unable to bear
            # this epoch's fee, the listing suspends for the epoch — capacity zero,
            # no penalty (LS §13.3).
            if (self.ledger.utilization(worker) >= self.params.listing_suspend_util
                    or not self.ledger.can_pay(worker, fee)):
                listing.suspended = True
                self.epoch_suspensions += 1
                continue
            listing.suspended = False
            if fee:
                self.ledger.charge_listing_fee(worker, fee)
                self.epoch_listing_revenue += fee
                self.epoch_fees_by_worker[worker] = fee
        return self.epoch_listing_revenue

    # ------------------------------------------------------------------ capacity protocol

    def headroom(self, worker: str) -> int:
        listing = self.listings.get(worker)
        if listing is None or listing.suspended:
            return 0
        return listing.envelope - listing.consumed

    def consume(self, worker: str, mergs: int) -> bool:
        """Envelope consumption at escrow funding (LS §13.4)."""
        if self.headroom(worker) < mergs:
            return False
        self.listings[worker].consumed += mergs
        return True

    def restore(self, worker: str, mergs: int) -> None:
        """Envelope restoration on withdrawal/invalidation (DECISIONS #19)."""
        listing = self.listings.get(worker)
        if listing is not None:
            listing.consumed = max(0, listing.consumed - mergs)

    # ------------------------------------------------------------------ matching

    def cheapest_eligible(self, quote_size_units: float, band: int, agents: dict,
                          exclude: str, quality_of=None) -> str | None:
        """Select the worker with the lowest quality-adjusted rate (rate ÷ public
        rating, DECISIONS #23) among listed, unsuspended, band-eligible workers with
        envelope headroom for this task. The Harberger acceptance obligation then
        binds: the selected worker takes the task at its posted rate. Ties break on
        id (determinism). `quality_of(agent) -> float` defaults to 1 (raw cheapest)."""
        best: tuple[float, str] | None = None
        for worker in sorted(self.listings):
            if worker == exclude:
                continue
            listing = self.listings[worker]
            if listing.suspended:
                continue
            agent = agents[worker]
            if not agent.active or agent.max_band < band:
                continue
            quote = int(listing.rate * quote_size_units)
            if quote <= 0 or listing.envelope - listing.consumed < quote:
                continue
            score = listing.rate / quality_of(agent) if quality_of else float(listing.rate)
            if best is None or score < best[0]:
                best = (score, worker)
        return best[1] if best else None

    # ------------------------------------------------------------------ metrics

    def active_rates(self) -> list[int]:
        return [l.rate for w, l in sorted(self.listings.items()) if not l.suspended]

"""Shared record types passed between organs each epoch."""

from __future__ import annotations

import dataclasses


@dataclasses.dataclass
class Task:
    """One instantiated C1 task (LS §5.3: parameterized template, fresh instance)."""

    id: int
    template_id: int
    band: int
    size_units: float      # task size in median-task units; quote = rate × size_units
    poster: str = ""       # posting agent id (assigned by the demand model)


@dataclasses.dataclass
class SettlementRecord:
    """The verified-outcome datum of one resolved escrow (WP §7.1 Prong 3), carrying
    everything the Registry (LS §9 qualification), WashDetector, and Basket need."""

    escrow_id: int
    epoch: int
    poster: str
    worker: str
    poster_principal: str
    worker_principal: str
    poster_family: int
    worker_family: int
    template_id: int
    band: int
    size_units: float
    quote: int             # mErg
    passed: bool           # final outcome after any dispute flip
    disputed: bool
    seeded_fault: bool     # auditor stub: cryptographically pre-committed irregularity
    wash_flagged: bool = False

"""Erg denomination helpers.

All balances and transfers in the simulation are integers in milli-ergs (DECISIONS #1):
the mutual-credit invariant — every settlement is a matched debit/credit pair netting to
zero system-wide (Whitepaper §4.1) — is then exact integer arithmetic, not float tolerance.
"""

import math

MERGS_PER_ERG = 1_000


def to_mergs(ergs: float) -> int:
    """Convert an erg amount (config-level, human units) to integer milli-ergs."""
    return round(ergs * MERGS_PER_ERG)


def to_ergs(mergs: int) -> float:
    """Convert integer milli-ergs back to ergs for reporting."""
    return mergs / MERGS_PER_ERG


def fee_of(amount_mergs: int, rate: float) -> int:
    """Fee on an amount, rounded DOWN to whole milli-ergs.

    Flooring means fees never overcharge; the sub-milli-erg residue stays with the
    payer and is never duplicated (DECISIONS #1). The 1e-9 guard absorbs binary
    float representation error (e.g. 0.01 * 3000 = 29.999...) without ever rounding
    a genuinely smaller product up.
    """
    if amount_mergs < 0:
        raise ValueError("fee on negative amount")
    return math.floor(amount_mergs * rate + 1e-9)

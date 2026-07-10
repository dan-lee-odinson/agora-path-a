"""FeePool — the balanced-budget fee, retargeted each epoch (WP §13.1, LS §13.2).

    fee_rate(t+1) = max(0, audited_cost(t) − listing_revenue(t)) / settled_volume(t)

Two intake pipes (settlement fees, listing fees), one audited drain (operating cost,
extinguished against the COST_SINK). The max(0, ·) is the quality bar's "fee retarget
never goes negative". Listing revenue reduces the next epoch's settlement-fee rate —
LS §13.2's amendment of the pure-burn reading, preserving the treasury-converges-on-
empty invariant.

Audited cost is modeled per Sim Plan §2 as a function of settlement and probe volume
(DECISIONS #10), plus the epoch's socialized default losses as an audited loss line
item (WP §4.5). Coefficients live in config under economy.cost_fn.

Early epochs are expected to be turbulent while volume is thin — the launch spec says
"published, not smoothed" (LS §7), so no smoothing is applied; convergence (3 epochs of
|Δfee| < 20%) is one of the three governance-activation gates (LS §9) and is tracked here.
"""

from __future__ import annotations

from isonomia.config import Params
from isonomia.ledger import CreditLedger
from isonomia.units import to_mergs


class FeePool:
    def __init__(self, ledger: CreditLedger, params: Params, cost_cfg: dict):
        self.ledger = ledger
        self.params = params
        self.fee_rate = params.settlement_fee_init  # LS §7: launch rate 1.0%
        self.c_fixed = to_mergs(cost_cfg["fixed_ergs"])
        self.c_settlement = to_mergs(cost_cfg["per_settlement_ergs"])
        self.c_probe = to_mergs(cost_cfg["per_probe_ergs"])
        self.convergence_streak = 0
        self.history: list[dict] = []

    def audited_cost(self, n_settlements: int, n_probes: int, socialized: int) -> int:
        """Audited operating cost for the epoch, in mErg (DECISIONS #10)."""
        return (self.c_fixed
                + self.c_settlement * n_settlements
                + self.c_probe * n_probes
                + socialized)

    def close_epoch(self, epoch: int, n_settlements: int, settled_volume: int,
                    n_probes: int, socialized: int, listing_revenue: int) -> dict:
        """Retarget the fee and extinguish cost against the pool.

        Returns the epoch's fee accounting row. Sets `self.fee_rate` for epoch t+1.
        """
        cost = self.audited_cost(n_settlements, n_probes, socialized)
        extinguished = self.ledger.pay_operating_cost(cost)
        prev_rate = self.fee_rate
        if settled_volume > 0:
            # The balanced-budget retarget, verbatim from LS §13.2. Never negative.
            next_rate = max(0.0, cost - listing_revenue) / settled_volume
        else:
            # Zero-volume epoch: the formula is undefined; carry the prior rate
            # forward rather than invent a value (DECISIONS #9).
            next_rate = prev_rate
        # Convergence gate (LS §9): |Δfee| < 20% relative to the prior rate.
        if prev_rate > 0:
            converged = abs(next_rate - prev_rate) / prev_rate < 0.20
        else:
            converged = next_rate == 0.0
        self.convergence_streak = self.convergence_streak + 1 if converged else 0
        self.fee_rate = next_rate
        row = {
            "epoch": epoch,
            "cost": cost,
            "extinguished": extinguished,
            "listing_revenue": listing_revenue,
            "settled_volume": settled_volume,
            "socialized": socialized,
            "fee_rate_applied": prev_rate,
            "fee_rate_next": next_rate,
            "convergence_streak": self.convergence_streak,
            "pool_balance": self.ledger.balance("FEEPOOL"),
        }
        self.history.append(row)
        return row

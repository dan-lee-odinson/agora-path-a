"""CreditLedger — the monetary core (Launch Spec §6: "no mint function exists").

Ergs are mutual credit (Whitepaper §4.1): no erg exists until a hire settles, and every
movement is a matched debit/credit pair. This module is the single place balances change;
`_transfer` is the only mutation point, so the system-wide zero-sum invariant is enforced
by construction and checked cheaply (`total() == 0`, exactly, in integer milli-ergs —
DECISIONS #1).

Credit policy is monetary policy (WP §4.5). The ledger implements:

  L_i = min( max(L_floor_active, α · V_i), L_cap )        (LS §7)
  L_floor_active = min(200, 30 × D_erg)                    collateralization invariant
  V_i = trailing 6-epoch worker-side settled volume        (DECISIONS #2, #3)

Default handling follows WP §4.5: bond forfeiture first (up to the deficit), audited
loss socialization second; the socialized remainder is returned to the caller so the
FeePool can carry it as a cost line item.

System accounts:
  ESCROW    — funded quotes in flight (Escrow module moves value in/out)
  FEEPOOL   — settlement + listing fee intake (FeePool module drains it)
  COST_SINK — extinguished operating expenditure (WP §13.1 "extinguished against cost")
  WRITEOFF  — matched entries for default write-offs and exit extinguishment; the only
              account allowed to run negative without a credit line (DECISIONS #11)
"""

from __future__ import annotations

from agora.config import Params

SYSTEM_ACCOUNTS = ("ESCROW", "FEEPOOL", "COST_SINK", "WRITEOFF")


class CreditError(Exception):
    """A transfer would breach a credit line or spend unheld system funds."""


class CreditLedger:
    def __init__(self, params: Params):
        self.params = params
        self.balances: dict[str, int] = {name: 0 for name in SYSTEM_ACCOUNTS}
        # worker-side settled volume per agent per epoch (feeds V_i; DECISIONS #3)
        self.earned: dict[str, dict[int, int]] = {}
        # per-epoch cached credit lines: recomputed at each epoch open
        self.lines: dict[str, int] = {}
        self.n_transfers = 0

    # ------------------------------------------------------------ accounts

    def register(self, agent_id: str) -> None:
        if agent_id in self.balances:
            raise ValueError(f"duplicate account {agent_id}")
        if agent_id in SYSTEM_ACCOUNTS:
            raise ValueError("reserved account name")
        self.balances[agent_id] = 0
        self.earned[agent_id] = {}
        self.lines[agent_id] = self.params.l_floor_active_mergs

    def balance(self, account: str) -> int:
        return self.balances[account]

    def total(self) -> int:
        """Exact system-wide sum; the mutual-credit invariant demands 0, always."""
        return sum(self.balances.values())

    # ------------------------------------------------------------ transfers

    def _transfer(self, src: str, dst: str, amount: int, *, credit_check: bool = True) -> None:
        """Sole balance-mutation point. Matched pair: debit src, credit dst."""
        if not isinstance(amount, int):
            raise TypeError("amounts are integer milli-ergs (DECISIONS #1)")
        if amount < 0:
            raise ValueError("negative transfer")
        if src == dst:
            raise ValueError("self-transfer")
        if src in ("ESCROW", "FEEPOOL", "COST_SINK"):
            # These system accounts spend only what they hold; only WRITEOFF may
            # go negative (it is the record of written-off debt, not a spender).
            if self.balances[src] < amount:
                raise CreditError(f"system account {src} lacks funds")
        elif src != "WRITEOFF" and credit_check:
            if self.balances[src] - amount < -self.lines[src]:
                raise CreditError(f"{src} would exceed credit line")
        self.balances[src] -= amount
        self.balances[dst] += amount
        self.n_transfers += 1

    # ------------------------------------------------------------ credit lines

    def refresh_lines(self, epoch: int, active_ids: list[str]) -> None:
        """Recompute L_i at epoch open from the trailing settled-volume window.

        The line for epoch t uses earned volume from epochs t−window .. t−1 —
        credit is sized to *demonstrated* flow (WP §4.5), never to the epoch
        in progress.
        """
        window = range(max(1, epoch - self.params.v_window_epochs), epoch)
        for agent_id in active_ids:
            volume = sum(self.earned[agent_id].get(e, 0) for e in window)
            line = min(
                max(self.params.l_floor_active_mergs, int(self.params.alpha * volume)),
                self.params.l_cap_mergs,
            )
            self.lines[agent_id] = line

    def credit_line(self, agent_id: str) -> int:
        return self.lines[agent_id]

    def available(self, agent_id: str) -> int:
        return self.balances[agent_id] + self.lines[agent_id]

    def can_pay(self, agent_id: str, amount: int) -> bool:
        return self.balances[agent_id] - amount >= -self.lines[agent_id]

    def utilization(self, agent_id: str) -> float:
        """Fraction of the credit line drawn; drives listing suspension (LS §13.3)."""
        if self.balances[agent_id] >= 0:
            return 0.0
        return -self.balances[agent_id] / self.lines[agent_id]

    # ------------------------------------------------------------ escrow flows

    def fund_escrow(self, buyer: str, amount: int) -> None:
        """Credit is drawn HERE — at escrow funding, not at settlement (LS §13.4)."""
        self._transfer(buyer, "ESCROW", amount)

    def settle_from_escrow(self, worker: str, quote: int, fee: int) -> None:
        """Matched-pair settlement: the buyer paid exactly the escrowed quote at
        funding (LS §13.1); the worker receives quote − fee and FeePool the fee
        (worker-side incidence, DECISIONS #4)."""
        if fee > quote:
            raise ValueError("fee exceeds quote")
        self._transfer("ESCROW", worker, quote - fee)
        if fee:
            self._transfer("ESCROW", "FEEPOOL", fee)

    def refund_from_escrow(self, poster: str, amount: int) -> None:
        self._transfer("ESCROW", poster, amount)

    def withdrawal_split(self, poster: str, worker: str, quote: int, reservation_fee: int) -> None:
        """Poster withdrawal after funding: 2% reservation fee to the WORKER
        (LS §13.4 — capacity griefing is priced), remainder refunded."""
        if reservation_fee:
            self._transfer("ESCROW", worker, reservation_fee)
        self._transfer("ESCROW", poster, quote - reservation_fee)

    # ------------------------------------------------------------ fees & cost

    def charge_listing_fee(self, agent_id: str, amount: int) -> None:
        """Listing fees may draw against the credit line — no carve-out (LS §13.3)."""
        self._transfer(agent_id, "FEEPOOL", amount)

    def pay_operating_cost(self, amount: int) -> int:
        """Extinguish fee intake against audited expenditure (WP §13.1). Pays what
        the pool holds; returns the amount actually extinguished."""
        paid = min(amount, self.balances["FEEPOOL"])
        if paid:
            self._transfer("FEEPOOL", "COST_SINK", paid)
        return paid

    # ------------------------------------------------------------ earned volume

    def record_earned(self, worker: str, epoch: int, amount: int) -> None:
        self.earned[worker][epoch] = self.earned[worker].get(epoch, 0) + amount

    def remove_earned(self, worker: str, epoch: int, amount: int) -> None:
        """Wash-flagged settlements do not demonstrate flow (DECISIONS #3)."""
        self.earned[worker][epoch] = self.earned[worker].get(epoch, 0) - amount

    # ------------------------------------------------------------ exit & default

    def handle_default(self, agent_id: str) -> tuple[int, int, int]:
        """Insolvent exit (WP §4.5): bond forfeiture first, socialization second.

        Returns (deficit, seized_from_bond, socialized). The account is zeroed
        against WRITEOFF; the socialized remainder becomes an audited loss line
        item in the next fee retarget (FeePool's job).
        """
        deficit = max(0, -self.balances[agent_id])
        seized = min(deficit, self.params.bond_value_mergs)
        socialized = deficit - seized
        if deficit:
            self._transfer("WRITEOFF", agent_id, deficit, credit_check=False)
        return deficit, seized, socialized

    def extinguish_exit(self, agent_id: str) -> int:
        """Positive balances are extinguished on exit — they do not convert
        outward (WP §4.2, §12). Returns the amount extinguished."""
        balance = self.balances[agent_id]
        if balance > 0:
            self._transfer(agent_id, "WRITEOFF", balance, credit_check=False)
        return max(0, balance)

    # ------------------------------------------------------------ metrics

    def agent_ids(self) -> list[str]:
        return sorted(k for k in self.balances if k not in SYSTEM_ACCOUNTS)

    def credit_outstanding(self) -> int:
        """Total drawn credit: the sum of negative agent balances, in magnitude.
        This is the numerator of the supply-stability kill criterion (LS §10)."""
        return sum(-b for k, b in self.balances.items() if k not in SYSTEM_ACCOUNTS and b < 0)

    def positive_supply(self) -> int:
        return sum(b for k, b in self.balances.items() if k not in SYSTEM_ACCOUNTS and b > 0)

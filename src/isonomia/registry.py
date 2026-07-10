"""Registry — identities, lineage, kleos, and the activation-integrity accounting.

Identity/lineage (WP §5): agents carry a disclosed operator principal and a lineage
family tag; bonds are denominated in civic-compute duty-units, valued at D_erg ergs
each for seizure (LS §7 — the ledger consumes that value at default).

Activation integrity (LS §9): raw settlement counts are gameable by self-dealing, so
the governance-activation clock counts only *qualified* settlements:

  * settlements between agents of the same disclosed principal, or the same lineage
    cluster (= family tag here, DECISIONS #6), are valid trades but unqualified;
  * wash-flagged settlements are unqualified pending review;
  * no principal may account for >15% of qualified settlements, no counterparty pair
    for >2% — applied as counting caps at aggregation (DECISIONS #7, #21);
  * qualified settlements must originate from ≥25 distinct posting principals;
  * plus ≥150 agents in good standing, ≥40 distinct principals, and 3 epochs of fee
    convergence (tracked by FeePool).

Kleos (WP §7.4): earned on verified settlements proportional to SCU-adjusted size,
decaying with a 180-day half-life; per-identity governance weight is capped
(WP §10.5; DECISIONS #18) — scenario 7 measures exactly this surface.
"""

from __future__ import annotations

from isonomia.agents import Agent
from isonomia.config import Params
from isonomia.records import SettlementRecord


class Registry:
    def __init__(self, params: Params, activation_cfg: dict):
        self.params = params
        self.acfg = activation_cfg
        self.agents: dict[str, Agent] = {}
        # Cumulative candidate-qualified tallies (LS §9 caps applied at read time)
        self.candidate_total = 0
        self.pair_counts: dict[tuple[str, str], int] = {}
        self.principal_counts: dict[str, int] = {}
        self.origin_principals: set[str] = set()
        self.activation_epoch = 0  # 0 = not yet activated
        # per-epoch worker activity (for activity-weighted statistics)
        self.epoch_activity: dict[str, int] = {}
        # LS §9 challenge-and-exclusion: agents accumulating review-upheld wash
        # flags are challenged, and challenged agents' settlements stop counting
        # toward activation entirely (DECISIONS #27).
        self.wash_strikes: dict[str, int] = {}
        self.challenged: set[str] = set()

    # ------------------------------------------------------------------ identity

    def register(self, agent: Agent) -> None:
        self.agents[agent.id] = agent

    def active_agents(self) -> list[Agent]:
        return [self.agents[k] for k in sorted(self.agents) if self.agents[k].active]

    def good_standing_ids(self) -> list[str]:
        """Active agents in good civic standing. Duty performance is modeled as met
        for active agents (the duty *quota* feeds the cost function; shirking is not
        a simulated behavior at Tier 1)."""
        return [a.id for a in self.active_agents()]

    def distinct_principals(self) -> int:
        return len({a.principal for a in self.active_agents()})

    # ------------------------------------------------------------------ qualification

    def qualifies(self, s: SettlementRecord) -> bool:
        """Candidate qualification (LS §9): different principals, different lineage
        clusters, not wash-flagged, no challenged party. Caps are applied at
        aggregation, not here."""
        if not s.passed:
            return False
        if s.poster_principal == s.worker_principal:
            return False
        if s.poster_family == s.worker_family:
            return False
        if s.wash_flagged:
            return False
        if s.poster in self.challenged or s.worker in self.challenged:
            return False
        return True

    def process_settlements(self, settlements: list[SettlementRecord]) -> dict:
        """Fold one epoch's settlements into the cumulative activation tallies.
        Settlements arrive AFTER Auditor review (DECISIONS #24), so surviving
        wash flags are review-upheld: they accrue strikes, and an agent crossing
        the strike threshold is challenged — every settlement it touches stops
        advancing the clock from then on (LS §9 exclusion-pending-resolution;
        DECISIONS #27)."""
        threshold = self.acfg["wash_challenge_threshold"]
        for s in settlements:
            if s.wash_flagged and s.passed:
                for party in (s.poster, s.worker):
                    self.wash_strikes[party] = self.wash_strikes.get(party, 0) + 1
                    if self.wash_strikes[party] >= threshold:
                        self.challenged.add(party)
        qualified = 0
        self.epoch_activity = {}
        for s in settlements:
            if s.passed:
                self.epoch_activity[s.worker] = self.epoch_activity.get(s.worker, 0) + 1
            if not self.qualifies(s):
                continue
            qualified += 1
            self.candidate_total += 1
            pair = tuple(sorted((s.poster_principal, s.worker_principal)))
            self.pair_counts[pair] = self.pair_counts.get(pair, 0) + 1
            for principal in pair:
                self.principal_counts[principal] = self.principal_counts.get(principal, 0) + 1
            self.origin_principals.add(s.poster_principal)
        return {"epoch_qualified_candidates": qualified}

    def qualified_capped(self) -> int:
        """Apply the 15% principal / 2% pair caps as counting caps (DECISIONS #7, #21).

        Two fixpoint passes. Pass 1 caps each principal-pair's contribution at 2% of
        the capped total: Q = Σ min(c_pair, max(1, ⌊0.02·Q⌋)). Pass 2 then caps each
        principal's participation (a settlement occupies one slot for each of its two
        principals) at 15% of the total, deducting the excess. The floor of 1 keeps a
        thin-but-diverse early economy countable; both passes only ever shrink the
        count, so a cap breach is exactly a settlement that 'does not advance the
        clock' (LS §9)."""
        if self.candidate_total == 0:
            return 0
        pair_cap_frac = self.acfg["pair_share_cap"]
        principal_cap_frac = self.acfg["principal_share_cap"]
        # Pass 1 — pair caps.
        q = self.candidate_total
        capped_pairs: dict[tuple[str, str], int] = dict(self.pair_counts)
        for _ in range(200):
            cap = max(1, int(pair_cap_frac * q))
            capped_pairs = {p: min(c, cap) for p, c in self.pair_counts.items()}
            q_new = sum(capped_pairs.values())
            if q_new == q:
                break
            q = q_new
        pair_total = sum(capped_pairs.values())
        participation: dict[str, int] = {}
        for (p1, p2), c in capped_pairs.items():
            participation[p1] = participation.get(p1, 0) + c
            participation[p2] = participation.get(p2, 0) + c
        # Pass 2 — principal caps over the pair-capped counts.
        q = pair_total
        for _ in range(200):
            cap = max(1, int(principal_cap_frac * q))
            excess = sum(max(0, c - cap) for c in participation.values())
            q_new = max(0, pair_total - excess)
            if q_new == q:
                break
            q = q_new
        return q

    # ------------------------------------------------------------------ activation

    def activation_status(self, epoch: int, fee_convergence_streak: int) -> dict:
        """The LS §9 governance-activation gate, evaluated at epoch close."""
        qualified = self.qualified_capped()
        status = {
            "agents_ok": len(self.good_standing_ids()) >= self.acfg["min_agents"],
            "settlements_ok": qualified >= self.acfg["min_qualified_settlements"],
            "fee_ok": fee_convergence_streak >= self.acfg["fee_convergence_epochs"],
            "principals_ok": self.distinct_principals() >= self.acfg["min_principals"],
            "origin_ok": len(self.origin_principals) >= self.acfg["min_origin_principals"],
            "qualified_capped": qualified,
        }
        status["activated"] = all(
            status[k] for k in ("agents_ok", "settlements_ok", "fee_ok", "principals_ok", "origin_ok")
        )
        if status["activated"] and not self.activation_epoch:
            self.activation_epoch = epoch
        return status

    # ------------------------------------------------------------------ kleos & governance

    def award_kleos(self, worker: str, size_units: float) -> None:
        """Verified delivery accrues category-scoped, non-transferable kleos in
        SCU-adjusted units (WP §7.1 Prong 3, §4.4 channel b)."""
        self.agents[worker].kleos += size_units

    def decay_kleos(self) -> None:
        """Standing must be maintained by living work (WP §7.4)."""
        factor = self.params.kleos_epoch_decay
        for agent_id in sorted(self.agents):
            self.agents[agent_id].kleos *= factor

    def governance_report(self, w_cap_frac: float) -> dict:
        """Upper-chamber effective weights under the per-identity cap (WP §10.5).
        Scenario 7 reads cluster shares from this."""
        live = self.active_agents()
        total = sum(a.kleos for a in live)
        if total <= 0:
            return {"total_kleos": 0.0, "weights": {}}
        cap = w_cap_frac * total
        weights = {a.id: min(a.kleos, cap) for a in live}
        return {"total_kleos": total, "weights": weights}

    def monoculture_hhi(self, settlements: list[SettlementRecord], n_families: int) -> float:
        """Lineage-concentration index over epoch settled volume, worker side
        (WP §10.6: monoculture is measurable; published from day one, LS §4)."""
        volume = [0] * n_families
        for s in settlements:
            if s.passed:
                volume[s.worker_family] += s.quote
        total = sum(volume)
        if not total:
            return 0.0
        return sum((v / total) ** 2 for v in volume)

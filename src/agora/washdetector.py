"""WashDetector — self-dealing pattern flags (LS §9).

Four detectors over each epoch's settlement graph, thresholds config-tunable
(Sim Plan §2):

  circular flow        A→B→A (and A→B→C→A) value loops within the epoch
  repeat counterparty  abnormal concentration of either party's settlements in one pair
  trivial-task spam    envelope-minimum-size tasks at statistically anomalous per-agent rates
  pass-rate anomaly    high-volume pairs with implausibly perfect pass rates

Flagged settlements are unqualified pending Auditor review (LS §9) — in the sim they
stay unqualified and their volume is removed from credit-line turnover (DECISIONS #3).
False positives on honest populations are a first-class output: a detector that
flags honest trade is itself a calibration failure, so the model logs flag counts on
known-honest agents every epoch.
"""

from __future__ import annotations

import math

from agora.records import SettlementRecord


class WashDetector:
    def __init__(self, det_cfg: dict):
        self.cfg = det_cfg

    def scan(self, settlements: list[SettlementRecord]) -> dict:
        """Flag this epoch's settlements in place. Returns per-detector counts."""
        settled = [s for s in settlements if s.passed]
        flags: dict[int, set[str]] = {}

        def flag(s: SettlementRecord, reason: str) -> None:
            flags.setdefault(s.escrow_id, set()).add(reason)
            s.wash_flagged = True

        # ---- circular flow -------------------------------------------------
        # The wash signature is a *value loop* (LS §9: "A→B→A value loops"): money
        # goes around and comes back roughly balanced, and the loop is a large
        # share of each member's trade. Mere reciprocity is NOT flagged — in a
        # closed mutual-credit economy honest agents both hire and work
        # (that is the LETS design, WP §4.1), so A↔B trade with unbalanced,
        # incidental values is normal commerce.
        balance_ratio = self.cfg["cycle_balance_ratio"]
        min_share = self.cfg["cycle_min_share"]
        pair_value: dict[tuple[str, str], int] = {}
        agent_volume: dict[str, int] = {}
        edges: dict[str, dict[str, int]] = {}
        for s in settled:
            pair_value[(s.poster, s.worker)] = pair_value.get((s.poster, s.worker), 0) + s.quote
            edges.setdefault(s.poster, {})
            edges[s.poster][s.worker] = edges[s.poster].get(s.worker, 0) + s.quote
            for party in (s.poster, s.worker):
                agent_volume[party] = agent_volume.get(party, 0) + s.quote
        flagged_pairs: set[tuple[str, str]] = set()
        for (a, b), v_ab in sorted(pair_value.items()):
            if a >= b or (b, a) not in pair_value:
                continue
            v_ba = pair_value[(b, a)]
            balance = min(v_ab, v_ba) / max(v_ab, v_ba)
            loop_value = v_ab + v_ba
            share = min(loop_value / agent_volume[a], loop_value / agent_volume[b])
            if balance >= balance_ratio and share >= min_share:
                flagged_pairs.add((a, b))
        three_cycle_edges: set[tuple[str, str]] = set()
        if self.cfg["cycle_max_len"] >= 3:
            for a in sorted(edges):
                for b in sorted(edges[a]):
                    for c in sorted(edges.get(b, {})):
                        if c == a or a not in edges.get(c, {}):
                            continue
                        v1, v2, v3 = edges[a][b], edges[b][c], edges[c][a]
                        if min(v1, v2, v3) / max(v1, v2, v3) < balance_ratio:
                            continue
                        cycle_value = v1 + v2 + v3
                        member_share = min(
                            (v1 + v3) / agent_volume[a],
                            (v1 + v2) / agent_volume[b],
                            (v2 + v3) / agent_volume[c],
                        )
                        if member_share >= min_share:
                            three_cycle_edges.update({(a, b), (b, c), (c, a)})
        for s in settled:
            key = tuple(sorted((s.poster, s.worker)))
            if key in flagged_pairs:
                flag(s, "circular2")
            if (s.poster, s.worker) in three_cycle_edges:
                flag(s, "circular3")

        # ---- repeat counterparty -------------------------------------------
        # Wash rings are MUTUALLY concentrated: each member's trade is dominated
        # by the ring. An honest star (one popular worker) is one-sided — the
        # poster leans on the worker, but the busy worker's share from any one
        # poster stays small — so the flag requires the concentration on BOTH
        # sides of the pair. This is what keeps honest-market concentration from
        # reading as wash (the false-positive rate on honest baselines is a
        # first-class calibration output).
        per_agent_total: dict[str, int] = {}
        per_agent_pair: dict[str, dict[str, int]] = {}
        for s in settled:
            for me, other in ((s.poster, s.worker), (s.worker, s.poster)):
                per_agent_total[me] = per_agent_total.get(me, 0) + 1
                per_agent_pair.setdefault(me, {})[other] = per_agent_pair.get(me, {}).get(other, 0) + 1
        # Sustained wash volume MUST recirculate value: under mutual credit a
        # one-way "ring" exhausts the payer's credit line within an epoch, so any
        # viable repeat-counterparty wash has flow in both directions. One-way
        # concentration is just a customer with a favorite supplier.
        hot_pairs: set[tuple[str, str]] = set()
        for me in sorted(per_agent_pair):
            for other, count in sorted(per_agent_pair[me].items()):
                if me >= other:
                    continue
                total = count  # settlements in either direction (already symmetric)
                bidirectional = (pair_value.get((me, other), 0) > 0
                                 and pair_value.get((other, me), 0) > 0)
                mutual_share = min(total / per_agent_total[me], total / per_agent_total[other])
                if (bidirectional and total >= self.cfg["repeat_pair_min"]
                        and mutual_share >= self.cfg["repeat_pair_share"]):
                    hot_pairs.add((me, other))
        for s in settled:
            if tuple(sorted((s.poster, s.worker))) in hot_pairs:
                flag(s, "repeat_pair")

        # ---- trivial-task spam ---------------------------------------------
        # Anomalous per-agent RATE of envelope-minimum tasks (LS §9): the z-score
        # runs on each agent's trivial *share* of its own settlements, not its raw
        # count — raw counts just measure activity, and busy honest workers are
        # not spammers.
        sizes = sorted(s.size_units for s in settled)
        if sizes:
            idx = max(0, int(self.cfg["trivial_size_quantile"] * len(sizes)) - 1)
            trivial_cut = sizes[idx]
            trivial_counts: dict[str, int] = {}
            for s in settled:
                if s.size_units <= trivial_cut:
                    for party in (s.poster, s.worker):
                        trivial_counts[party] = trivial_counts.get(party, 0) + 1
            eligible = [a for a in sorted(per_agent_total) if per_agent_total[a] >= 5]
            shares = {a: trivial_counts.get(a, 0) / per_agent_total[a] for a in eligible}
            if len(eligible) >= 8:
                mean = sum(shares.values()) / len(shares)
                var = sum((v - mean) ** 2 for v in shares.values()) / len(shares)
                sd = math.sqrt(var)
                if sd > 1e-9:
                    # A spammer's business IS envelope-minimum tasks: besides being
                    # a statistical outlier, the agent's trade must actually be
                    # dominated by trivial tasks (share/count floors) — a lognormal
                    # task mix always has z-tail agents, and they are not spammers.
                    spammers = {
                        a for a, v in shares.items()
                        if (v - mean) / sd >= self.cfg["trivial_rate_z"]
                        and v >= self.cfg["trivial_min_share"]
                        and trivial_counts.get(a, 0) >= self.cfg["trivial_min_count"]
                    }
                    for s in settled:
                        if s.size_units <= trivial_cut and (s.poster in spammers or s.worker in spammers):
                            flag(s, "trivial_spam")

        # ---- pass-rate anomaly ----------------------------------------------
        # High-volume, perfectly-passing pairs that are also mutually concentrated
        # (half the repeat-pair threshold): a reliable honest worker passes a lot
        # everywhere; a wash pair passes perfectly *at each other*.
        pair_outcomes: dict[tuple[str, str], list[bool]] = {}
        for s in settlements:  # includes failed verifications: the denominator matters
            pair_outcomes.setdefault(tuple(sorted((s.poster, s.worker))), []).append(s.passed)
        pair_ns = [len(v) for v in pair_outcomes.values()]
        if len(pair_ns) >= 8:
            mean_n = sum(pair_ns) / len(pair_ns)
            sd_n = math.sqrt(sum((n - mean_n) ** 2 for n in pair_ns) / len(pair_ns))
            if sd_n > 0:
                for pair in sorted(pair_outcomes):
                    outcomes = pair_outcomes[pair]
                    a, b = pair
                    if a not in per_agent_total or b not in per_agent_total:
                        continue
                    bidirectional = (pair_value.get((a, b), 0) > 0
                                     and pair_value.get((b, a), 0) > 0)
                    mutual_share = min(len(outcomes) / per_agent_total[a],
                                       len(outcomes) / per_agent_total[b])
                    z = (len(outcomes) - mean_n) / sd_n
                    if (bidirectional
                            and z >= self.cfg["pass_rate_z"]
                            and len(outcomes) >= self.cfg["repeat_pair_min"]
                            and mutual_share >= self.cfg["repeat_pair_share"] / 2
                            and sum(outcomes) / len(outcomes) >= 0.98):
                        for s in settled:
                            if tuple(sorted((s.poster, s.worker))) == pair:
                                flag(s, "pass_anomaly")

        reasons = [r for rs in flags.values() for r in rs]
        return {
            "flagged": len(flags),
            "circular": sum(1 for r in reasons if r.startswith("circular")),
            "repeat_pair": reasons.count("repeat_pair"),
            "trivial_spam": reasons.count("trivial_spam"),
            "pass_anomaly": reasons.count("pass_anomaly"),
        }

"""The discrete-epoch model loop (Sim Plan §2): 26 epochs of 14 days, seed-controlled.

Epoch sequence (PLAN.md):
  1. credit-line refresh from trailing settled volume
  2. listing phase: β fees, LS §13.3 suspension guard
  3. demand generation (exogenous inflow, optional shock multiplier)
  4. matching + escrow funding (capacity consumed at funding, LS §13.4)
  5. withdrawals (2% reservation fee to the worker)
  6. delivery + verification + stochastic Tier-1 disputes → matched-pair settlement
  7. civic-duty probe accounting (cost-function input)
  8. defaulter exits (policy-driven, milestone 4+): bond seizure, loss socialization
  9. wash detection → qualification + turnover adjustments
 10. fee retarget (LS §13.2), activation-clock update (LS §9)
 11. basket retarget at the close of epoch 6 (LS §5.4)
 12. kleos decay; metrics row; ledger invariant checks

Invariant checks run every epoch and any violation is recorded — a violation is the
sim-level analogue of an Adversary "settlement forgery / credit-line inflation"
finding, which is an immediate kill criterion (LS §10; DECISIONS #16).
"""

from __future__ import annotations

import hashlib
import json
import math

from agora import agents as policies
from agora.agents import Agent, build_population, rating
from agora.basket import Basket
from agora.config import Params
from agora.escrow import Escrow
from agora.feepool import FeePool
from agora.ledger import CreditLedger
from agora.listing import ListingMarket
from agora.records import SettlementRecord, Task
from agora.registry import Registry
from agora.rng import RngHub
from agora.runlog import RunLog
from agora.units import to_ergs
from agora.washdetector import WashDetector


def config_fingerprint(cfg: dict) -> str:
    """Stable hash of the full config — the reproducibility identity of a run."""
    blob = json.dumps(cfg, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(blob).hexdigest()[:16]


def _poisson(rng, lam: float) -> int:
    """Poisson draw; normal approximation above λ=30 (exact Knuth underflows there)."""
    if lam <= 0:
        return 0
    if lam > 30:
        return max(0, round(rng.gauss(lam, math.sqrt(lam))))
    threshold = math.exp(-lam)
    k, p = 0, 1.0
    while True:
        p *= rng.random()
        if p <= threshold:
            return k
        k += 1


def _corr(xs: list[float], ys: list[float]) -> float:
    """Pearson correlation; 0.0 when undefined (n<3 or zero variance)."""
    n = len(xs)
    if n < 3:
        return 0.0
    mx, my = sum(xs) / n, sum(ys) / n
    sxx = sum((x - mx) ** 2 for x in xs)
    syy = sum((y - my) ** 2 for y in ys)
    if sxx <= 0 or syy <= 0:
        return 0.0
    sxy = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    return sxy / math.sqrt(sxx * syy)


class Model:
    def __init__(self, cfg: dict, run_name: str | None = None):
        self.cfg = cfg
        self.params = Params.from_config(cfg)
        self.n_epochs = int(cfg["run"]["epochs"])
        self.seed = int(cfg["run"]["master_seed"])
        self.hub = RngHub(self.seed)
        self.economy = cfg["economy"]
        self.n_families = cfg["population"]["lineage_families"]

        # --- organs (the LS §6 contract set) ---------------------------------
        self.agents_list = build_population(cfg, self.hub)
        self.agents = {a.id: a for a in self.agents_list}
        self.ledger = CreditLedger(self.params)
        median_skill = sorted(a.skill for a in self.agents_list)[len(self.agents_list) // 2]
        self.basket = Basket(cfg, self.hub, median_skill)
        self.escrow = Escrow(self.ledger, self.params)
        self.listing = ListingMarket(self.ledger, self.params)
        self.feepool = FeePool(self.ledger, self.params, self.economy["cost_fn"])
        self.registry = Registry(self.params, cfg["activation"])
        self.detector = WashDetector(cfg["detector"])

        for agent in self.agents_list:
            self.ledger.register(agent.id)
            self.registry.register(agent)
            self.basket.examine(agent)

        self._set_initial_listings()

        # --- bookkeeping ------------------------------------------------------
        self.run_name = run_name or f"{cfg['meta']['name']}_s{self.seed}"
        events = cfg.get("logging", {}).get("events", True)
        self.log = RunLog(cfg["run"].get("out_dir", "results"), self.run_name, events_enabled=events)
        self.epoch = 0
        self.invariant_violations: list[str] = []
        self.total_defaults = 0
        self.total_socialized = 0
        self.activation_epoch = 0
        self.last_mean_rate = 0  # market price signal available to policies (mErg)
        self._mean_pass_cache: dict[str, float] = {}
        self.settlements_by_epoch: list[list[SettlementRecord]] = []

    # ------------------------------------------------------------------ setup

    def _set_initial_listings(self) -> None:
        """Genesis listings per policy (Sim Plan §3): honest self-assessment for most,
        deliberate mis-assessment for the Harberger test population, and marginal
        agents unlisted until the market clears their reservation price."""
        policies.init_policy_state(self.agents_list, self.cfg, self.hub)
        n_workers = max(1, len(self.agents_list))
        expected = self.economy["demand_tasks_per_epoch"] / n_workers
        default_capacity = max(self.params.capacity_min_tasks, math.ceil(1.6 * expected))
        for agent in self.agents_list:
            agent.rate_mergs = policies.initial_rate(agent)
            agent.capacity_tasks = 0 if agent.policy == "marginal" else default_capacity
            self.listing.set_listing(agent.id, agent.rate_mergs, agent.capacity_tasks)

    # ------------------------------------------------------------------ loop

    def run(self) -> dict:
        for epoch in range(1, self.n_epochs + 1):
            self.epoch = epoch
            self.step(epoch)
        summary = self.summarize()
        self.log.finalize(summary)
        return summary

    # Behavior-policy hooks — delegate to agents.py; scenarios may override.
    def policy_update_listings(self, epoch: int) -> None:
        if epoch >= 2:  # genesis listings stand for epoch 1
            policies.update_listings(self, epoch)

    def policy_generate_cascades(self, epoch: int, rng, funded_wave1: list) -> list[Task]:
        return policies.generate_cascades(self, epoch, rng, funded_wave1)

    def policy_process_exits(self, epoch: int, rng) -> tuple[int, int]:
        """Returns (defaults, socialized_mergs) this epoch."""
        return policies.process_exits(self, epoch, rng)

    def step(self, epoch: int) -> None:
        params = self.params
        # 1. credit lines from demonstrated flow (WP §4.5)
        active_ids = [a.id for a in self.agents_list if a.active]
        self.ledger.refresh_lines(epoch, active_ids)

        # 2. listing phase
        self.policy_update_listings(epoch)
        self.escrow.reset_epoch_counters()
        listing_revenue = self.listing.open_epoch()
        for worker_id, fee in self.listing.epoch_fees_by_worker.items():
            self.agents[worker_id].epoch_listing_fee_mergs += fee

        # 3. demand
        demand_rng = self.hub.stream(f"demand.e{epoch}")
        shock = self.economy["demand_shock"]
        multiplier = shock["multiplier"] if (shock["enabled"] and epoch in shock["epochs"]) else 1.0
        n_tasks = _poisson(demand_rng, self.economy["demand_tasks_per_epoch"] * multiplier)
        # Budget-weighted assignment (DECISIONS #22): a posting principal's budget is
        # its agent's funding headroom; broke posters originate no demand. Rational
        # posters keep a buffer above the LS §13.3 suspension threshold — spending
        # the last 10% of the line would lock them out of listing (and therefore
        # out of earning their way back). Exiting defaulters have no such scruple:
        # they burn the whole line, boosted.
        boost = self.economy["policies"]["exit_spend_boost"]
        posters = [a.id for a in self.agents_list if a.active and a.is_poster]
        weights = []
        for p in posters:
            if self.agents[p].exiting:
                weights.append(max(0, self.ledger.available(p)) * boost)
            else:
                buffer = int(0.15 * self.ledger.credit_line(p))
                weights.append(max(0, self.ledger.available(p) - buffer))
        tasks: list[Task] = []
        if posters and sum(weights) > 0:
            for _ in range(n_tasks):
                task = self.basket.instantiate(demand_rng, self.economy)
                task.poster = demand_rng.choices(posters, weights=weights)[0]
                tasks.append(task)

        # 4. matching + escrow funding (LS §13.4: capacity consumed here).
        # Posters pick the lowest quality-adjusted rate (DECISIONS #23) — this is
        # the channel through which reputation confers pricing power (WP §4.4c).
        quality_of = lambda agent: max(0.05, rating(agent, params.k_prior))  # noqa: E731

        def match_and_fund(task_list: list[Task]) -> tuple[list[tuple], int]:
            wave_funded: list[tuple] = []
            wave_unmatched = 0
            for task in task_list:
                worker_id = self.listing.cheapest_eligible(task.size_units, task.band, self.agents,
                                                           exclude=task.poster, quality_of=quality_of)
                if worker_id is None:
                    wave_unmatched += 1
                    continue
                quote = int(self.listing.get(worker_id).rate * task.size_units)
                if quote <= 0:
                    wave_unmatched += 1
                    continue
                record = self.escrow.fund(task.poster, worker_id, quote, task.band, epoch,
                                          capacity=self.listing)
                if record is not None:
                    wave_funded.append((record, task))
            return wave_funded, wave_unmatched

        funded, unmatched = match_and_fund(tasks)
        # Wave 2: orchestrator cascades, one level deep (WP §9.5; Sim Plan §3).
        cascade_tasks = self.policy_generate_cascades(epoch, demand_rng, funded)
        cascade_funded, cascade_unmatched = match_and_fund(cascade_tasks)
        funded.extend(cascade_funded)
        unmatched += cascade_unmatched
        tasks.extend(cascade_tasks)

        # 5. withdrawals (benign baseline rate; griefing scenarios raise it)
        withdraw_rng = self.hub.stream(f"withdraw.e{epoch}")
        in_flight = []
        for record, task in funded:
            if withdraw_rng.random() < self.economy["poster_withdrawal_rate"]:
                fee = self.escrow.withdraw(record, capacity=self.listing)
                self.agents[record.worker].epoch_earned_mergs += fee
            else:
                in_flight.append((record, task))

        # 6. delivery + verification + stochastic disputes (DECISIONS #14)
        delivery_rng = self.hub.stream(f"delivery.e{epoch}")
        audit_rng = self.hub.stream(f"audit.e{epoch}")
        dispute_cfg = self.economy["dispute"]
        settlements: list[SettlementRecord] = []
        disputes = overturns = seeded = detected = 0
        for record, task in in_flight:
            worker = self.agents[record.worker]
            template = self.basket.template(task.template_id)
            passed = delivery_rng.random() < self.basket.pass_prob(worker, template)
            disputed = delivery_rng.random() < dispute_cfg["rate"]
            if disputed:
                disputes += 1
                if delivery_rng.random() < dispute_cfg["overturn"]:
                    passed = not passed
                    overturns += 1
            seeded_fault = audit_rng.random() < params.seed_fault_rate
            if seeded_fault:
                seeded += 1
                if audit_rng.random() < params.auditor_sensitivity:
                    detected += 1
            fee = self.escrow.settle(record, passed, self.feepool.fee_rate)
            worker.delivered_n += 1
            worker.delivered_pass += (passed - worker.delivered_pass) / worker.delivered_n
            worker.epoch_work_cost_mergs += int(worker.unit_cost_mergs * task.size_units)
            self.basket.record_outcome(task.template_id, passed)
            if passed:
                worker.epoch_earned_mergs += record.quote - fee
                self.registry.award_kleos(record.worker, task.size_units)
            poster = self.agents[record.poster]
            settlements.append(SettlementRecord(
                escrow_id=record.id, epoch=epoch,
                poster=record.poster, worker=record.worker,
                poster_principal=poster.principal, worker_principal=worker.principal,
                poster_family=poster.family, worker_family=worker.family,
                template_id=task.template_id, band=task.band, size_units=task.size_units,
                quote=record.quote, passed=passed, disputed=disputed, seeded_fault=seeded_fault,
            ))

        # 7. civic-duty probe volume (WP §6; feeds the cost function)
        n_active = sum(1 for a in self.agents_list if a.active)
        probes = params.duty_quota * n_active

        # 8. defaulter exits (policies, milestone 4+)
        defaults, socialized = self.policy_process_exits(epoch, self.hub.stream(f"exit.e{epoch}"))
        self.total_defaults += defaults
        self.total_socialized += socialized

        # 9. wash detection → Auditor review → qualification and turnover
        # adjustments. LS §9: flagged settlements are unqualified PENDING Auditor
        # review; the review is modeled through the auditor stub's sensitivity
        # (DECISIONS #24): honest flags are cleared w.p. sensitivity, adversarial
        # flags survive w.p. sensitivity. Raw flags measure detector calibration;
        # the residual measures what the system actually suffers.
        wash_counts = self.detector.scan(settlements)
        if wash_counts["flagged"]:
            self.log.event("wash", epoch, **{k: v for k, v in wash_counts.items()})
        review_rng = self.hub.stream(f"washreview.e{epoch}")
        false_pos = 0
        fp_residual = 0
        for s in settlements:
            if not (s.wash_flagged and s.passed):
                continue
            adversarial = (self.agents[s.poster].policy.startswith("adv_")
                           or self.agents[s.worker].policy.startswith("adv_"))
            if adversarial:
                if review_rng.random() > params.auditor_sensitivity:
                    s.wash_flagged = False  # review wrongly clears the wash trade
            else:
                false_pos += 1
                if review_rng.random() < params.auditor_sensitivity:
                    s.wash_flagged = False  # review correctly clears honest trade
                else:
                    fp_residual += 1
            if s.wash_flagged:
                self.ledger.remove_earned(s.worker, epoch, s.quote)

        # 10. activation accounting + fee retarget
        epoch_qual = self.registry.process_settlements(settlements)
        n_settled = self.escrow.epoch_counters["settled"]
        settled_volume = self.escrow.epoch_counters["settled_volume"]
        fee_row = self.feepool.close_epoch(epoch, n_settled, settled_volume, probes, socialized, listing_revenue)
        activation = self.registry.activation_status(epoch, self.feepool.convergence_streak)
        if activation["activated"] and not self.activation_epoch:
            self.activation_epoch = epoch

        # 11. the single scheduled basket retarget (LS §5.4)
        if epoch == params.retarget_epoch:
            result = self.basket.retarget(epoch, params.retire_pass_threshold)
            self._mean_pass_cache.clear()
            self.log.event("retarget", epoch, **{k: v for k, v in result.items() if k != "epoch"})

        # 12. kleos decay + policy snapshots + metrics + invariants
        self.registry.decay_kleos()
        policies.capture_epoch_economics(self)
        rates_now = self.listing.active_rates()
        self.last_mean_rate = int(sum(rates_now) / len(rates_now)) if rates_now else 0
        self.settlements_by_epoch.append(settlements)
        self._check_invariants(epoch)
        self._emit_epoch_row(
            epoch=epoch, n_active=n_active, tasks_posted=len(tasks), unmatched=unmatched,
            settlements=settlements, disputes=disputes, overturns=overturns,
            seeded=seeded, detected=detected, probes=probes,
            defaults=defaults, socialized=socialized,
            listing_revenue=listing_revenue, fee_row=fee_row, activation=activation,
            wash_counts=wash_counts, wash_false_pos=false_pos, wash_fp_residual=fp_residual,
            epoch_qual=epoch_qual, n_cascade_tasks=len(cascade_tasks),
        )

    # ------------------------------------------------------------------ metrics

    def _agent_mean_pass(self, agent: Agent) -> float:
        if agent.id not in self._mean_pass_cache:
            self._mean_pass_cache[agent.id] = self.basket.agent_mean_pass(agent)
        return self._mean_pass_cache[agent.id]

    def _policy_markup(self, policy: str) -> float:
        """Mean posted-rate / believed-cost over this policy's live listings — the
        Harberger convergence observable (Sim Plan §1.2): does each pricing strategy
        get pushed toward delivered-quality-consistent levels?"""
        ratios = []
        for agent in self.agents_list:
            if agent.policy != policy or not agent.active:
                continue
            listing = self.listing.get(agent.id)
            if listing is None or listing.suspended:
                continue
            ratios.append(listing.rate / agent.unit_cost_mergs)
        return sum(ratios) / len(ratios) if ratios else 0.0

    def _emit_epoch_row(self, *, epoch, n_active, tasks_posted, unmatched, settlements,
                        disputes, overturns, seeded, detected, probes, defaults, socialized,
                        listing_revenue, fee_row, activation, wash_counts, wash_false_pos,
                        wash_fp_residual, epoch_qual, n_cascade_tasks) -> None:
        counters = self.escrow.epoch_counters
        settled_volume = counters["settled_volume"]
        credit_out = self.ledger.credit_outstanding()

        # Harberger observables (Sim Plan §1.2): price dispersion + price↔quality
        rates = self.listing.active_rates()
        mean_rate = sum(rates) / len(rates) if rates else 0.0
        if len(rates) >= 3 and mean_rate > 0:
            var = sum((r - mean_rate) ** 2 for r in rates) / len(rates)
            rate_cv = math.sqrt(var) / mean_rate
        else:
            rate_cv = 0.0
        xs, ys = [], []
        for agent_id in sorted(self.listing.listings):
            agent = self.agents[agent_id]
            listing = self.listing.listings[agent_id]
            if agent.delivered_n >= 3 and not listing.suspended:
                xs.append(float(listing.rate))
                ys.append(agent.delivered_pass)
        price_quality = _corr(xs, ys)

        # Activity-weighted median-agent pass estimate (WP §4.3 median defense)
        activity = self.registry.epoch_activity
        if activity:
            weight_sum = sum(activity.values())
            pass_est = sum(self._agent_mean_pass(self.agents[w]) * n for w, n in sorted(activity.items())) / weight_sum
        else:
            pass_est = 0.0

        n_settled = counters["settled"]
        resolved = n_settled + counters["failed_verification"]
        self.log.epoch_row({
            "epoch": epoch,
            "n_active": n_active,
            "fee_rate_applied": f"{fee_row['fee_rate_applied']:.6f}",
            "fee_rate_next": f"{fee_row['fee_rate_next']:.6f}",
            "fee_convergence_streak": fee_row["convergence_streak"],
            "listing_revenue_ergs": f"{to_ergs(listing_revenue):.3f}",
            "suspensions": self.listing.epoch_suspensions,
            "tasks_posted": tasks_posted,
            "unmatched": unmatched,
            "funding_failures": counters["funding_failures"],
            "funded": counters["funded"],
            "withdrawn": counters["withdrawn"],
            "settled": n_settled,
            "failed_verification": counters["failed_verification"],
            "pass_rate": f"{(n_settled / resolved):.4f}" if resolved else "0.0000",
            "settled_volume_ergs": f"{to_ergs(settled_volume):.3f}",
            "credit_outstanding_ergs": f"{to_ergs(credit_out):.3f}",
            "credit_to_volume": f"{(credit_out / settled_volume):.4f}" if settled_volume else "0.0000",
            "positive_supply_ergs": f"{to_ergs(self.ledger.positive_supply()):.3f}",
            "feepool_balance_ergs": f"{to_ergs(fee_row['pool_balance']):.3f}",
            "cost_ergs": f"{to_ergs(fee_row['cost']):.3f}",
            "defaults": defaults,
            "socialized_ergs": f"{to_ergs(socialized):.3f}",
            "socialization_rate": f"{(socialized / settled_volume):.5f}" if settled_volume else "0.00000",
            "dispute_rate": f"{(disputes / resolved):.4f}" if resolved else "0.0000",
            "overturns": overturns,
            "qualified_epoch": epoch_qual["epoch_qualified_candidates"],
            "qualified_capped_cum": activation["qualified_capped"],
            "act_agents_ok": int(activation["agents_ok"]),
            "act_settlements_ok": int(activation["settlements_ok"]),
            "act_fee_ok": int(activation["fee_ok"]),
            "act_principals_ok": int(activation["principals_ok"]),
            "act_origin_ok": int(activation["origin_ok"]),
            "activated": int(activation["activated"]),
            "monoculture_hhi": f"{self.registry.monoculture_hhi(settlements, self.n_families):.4f}",
            "wash_flagged": wash_counts["flagged"],
            "wash_false_pos": wash_false_pos,
            "wash_fp_residual": wash_fp_residual,
            "mean_rate_ergs": f"{to_ergs(int(mean_rate)):.3f}",
            "rate_cv": f"{rate_cv:.4f}",
            "price_quality_corr": f"{price_quality:.4f}",
            "basket_mean_difficulty": f"{self.basket.mean_active_difficulty():.4f}",
            "scu_index": f"{self.basket.scu_index:.6f}",
            "median_agent_pass_est": f"{pass_est:.4f}",
            "auditor_seeded": seeded,
            "auditor_detected": detected,
            "auditor_recall": f"{(detected / seeded):.4f}" if seeded else "1.0000",
            "probes": probes,
            "cascade_tasks": n_cascade_tasks,
            "markup_honest": f"{self._policy_markup('honest'):.4f}",
            "markup_overstater": f"{self._policy_markup('overstater'):.4f}",
            "markup_understater": f"{self._policy_markup('understater'):.4f}",
            "markup_adaptive": f"{self._policy_markup('adaptive'):.4f}",
            "marginal_listed": sum(
                1 for a in self.agents_list
                if a.policy == "marginal" and a.active and self.listing.get(a.id) is not None
            ),
            "invariant_violations": len(self.invariant_violations),
        })

    def _check_invariants(self, epoch: int) -> None:
        """DECISIONS #16: violations here are the Adversary-finding kill criterion."""
        if self.ledger.total() != 0:
            self.invariant_violations.append(f"e{epoch}: ledger sum {self.ledger.total()} != 0")
        if self.ledger.balance("ESCROW") != 0:
            self.invariant_violations.append(f"e{epoch}: ESCROW nonzero at epoch close")
        if self.ledger.balance("FEEPOOL") < 0 or self.ledger.balance("COST_SINK") < 0:
            self.invariant_violations.append(f"e{epoch}: system account negative")
        cap = self.params.l_cap_mergs
        for agent_id in self.ledger.agent_ids():
            if self.ledger.balance(agent_id) < -cap:
                self.invariant_violations.append(f"e{epoch}: {agent_id} beyond hard cap")
                break

    # ------------------------------------------------------------------ summary

    def summarize(self) -> dict:
        rows = self.log.epoch_rows
        family_counts: dict[str, int] = {}
        for agent in self.agents_list:
            family_counts[str(agent.family)] = family_counts.get(str(agent.family), 0) + 1
        return {
            "run_name": self.run_name,
            "config_fingerprint": config_fingerprint(self.cfg),
            "master_seed": self.seed,
            "epochs": self.n_epochs,
            "n_agents": len(self.agents_list),
            "n_principals": len({a.principal for a in self.agents_list}),
            "family_counts": family_counts,
            "policy_counts": {
                p: sum(1 for a in self.agents_list if a.policy == p)
                for p in sorted({a.policy for a in self.agents_list})
            },
            "total_settled": sum(int(r["settled"]) for r in rows),
            "total_settled_volume_ergs": round(sum(float(r["settled_volume_ergs"]) for r in rows), 3),
            "total_defaults": self.total_defaults,
            "total_socialized_ergs": to_ergs(self.total_socialized),
            "final_fee_rate": float(rows[-1]["fee_rate_next"]) if rows else None,
            "final_credit_to_volume": float(rows[-1]["credit_to_volume"]) if rows else None,
            "qualified_capped_final": int(rows[-1]["qualified_capped_cum"]) if rows else 0,
            "activation_epoch": self.activation_epoch,
            "scu_index_final": float(rows[-1]["scu_index"]) if rows else 1.0,
            "retargets": self.basket.retarget_log,
            "invariant_violations": self.invariant_violations,
        }

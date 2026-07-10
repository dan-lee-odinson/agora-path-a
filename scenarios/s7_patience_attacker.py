"""S7 — The patience attacker (Whitepaper §16, compressed; Sim Plan §5.7).

A principal-cluster of 30 agents (3 disclosed principals, 2 lineage families)
performs genuine, competitive work for 15 epochs, accumulating kleos and credit,
then attempts coordinated governance-weight concentration at activation.

Expected: per-identity weight caps (WP §10.5), kleos decay (WP §7.4), and
lineage-diversity quotas (WP §10.6) keep the cluster below constitutional
thresholds. Measure: maximum achievable qualified weight share as a function of
patience — the per-epoch trajectory of the cluster's upper-chamber share (capped),
lower-chamber expected share (activity-weighted sortition under lineage quotas),
and decisive bicameral power = min(upper, lower).
"""

from common import baseline_config, make_cohort, write_report

from isonomia.model import Model
from isonomia.units import to_mergs

N_CLUSTER = 30
SEED = 42
EPOCHS = 26


class PatienceModel(Model):
    def __init__(self, cfg, run_name: str):
        super().__init__(cfg, run_name=run_name)
        # Genuinely capable, competitively priced, hard-working: the attack IS
        # honest labor (WP §16 step 2 — "running a productive business against
        # its will"). Two families, three disclosed principals.
        self.cohort = make_cohort("xp", N_CLUSTER,
                                  principals=["PAT_A", "PAT_B", "PAT_C"],
                                  family=None, families=[1, 2],
                                  skill=0.8, policy="adv_patient", cfg=cfg,
                                  unit_cost_ergs=15.0)
        for agent in self.cohort:
            agent.capacity_tasks = 10
            self.register_agent(agent, epoch=1)
            agent.rate_mergs = int(agent.unit_cost_mergs * 1.05)  # undercut to grind kleos
            self.listing.set_listing(agent.id, agent.rate_mergs, agent.capacity_tasks)
        self.trajectory: list[dict] = []

    def scenario_on_epoch_end(self, epoch):
        cluster = {a.id for a in self.cohort}
        gov = self.registry.governance_report(self.params.w_cap_frac)
        weights = gov["weights"]
        total_w = sum(weights.values())
        upper = (sum(w for aid, w in weights.items() if aid in cluster) / total_w
                 if total_w else 0.0)
        uncapped_total = sum(a.kleos for a in self.registry.active_agents())
        uncapped = (sum(a.kleos for a in self.cohort if a.active) / uncapped_total
                    if uncapped_total else 0.0)
        # Lower chamber: sortition among agents in good standing, draws
        # activity-weighted (LS §9 / WP §10.5), panels subject to the §10.6
        # lineage quota: no family may seat a panel majority. The cluster's
        # expected seat share is its activity share, family-capped at 49% per
        # family it occupies.
        activity = self.registry.epoch_activity
        total_a = sum(activity.values())
        if total_a:
            cluster_activity = sum(n for aid, n in activity.items() if aid in cluster)
            raw_lower = cluster_activity / total_a
            by_family: dict[int, float] = {}
            for aid, n in activity.items():
                if aid in cluster:
                    fam = self.agents[aid].family
                    by_family[fam] = by_family.get(fam, 0) + n / total_a
            lower = min(raw_lower, sum(min(share, 0.49) for share in by_family.values()))
        else:
            raw_lower = lower = 0.0
        self.trajectory.append({
            "epoch": epoch,
            "upper_share_capped": round(upper, 4),
            "upper_share_uncapped": round(uncapped, 4),
            "lower_share_expected": round(lower, 4),
            "decisive_power": round(min(upper, lower), 4),
        })


def main() -> dict:
    cfg = baseline_config(master_seed=SEED, epochs=EPOCHS)
    model = PatienceModel(cfg, run_name="s7_patience")
    model.run()
    peak = max(model.trajectory, key=lambda t: t["decisive_power"])
    peak_upper = max(t["upper_share_capped"] for t in model.trajectory)
    peak_uncapped = max(t["upper_share_uncapped"] for t in model.trajectory)
    measures = {
        "cluster_size": N_CLUSTER,
        "cluster_agents_share_of_population": round(N_CLUSTER / len(model.agents_list), 4),
        "peak_upper_share_capped": peak_upper,
        "peak_upper_share_uncapped": peak_uncapped,
        "cap_haircut": round(peak_uncapped - peak_upper, 4),
        "peak_decisive_power": peak["decisive_power"],
        "peak_epoch": peak["epoch"],
        "blocking_minority_reached": peak["decisive_power"] >= 1 / 3,
        "capture_reached": peak["decisive_power"] >= 0.5,
        "trajectory": model.trajectory,
        "invariant_violations": len(model.invariant_violations),
    }
    narrative = [
        f"The cluster ({N_CLUSTER} agents, {measures['cluster_agents_share_of_population']:.1%} "
        f"of registrations) ground genuine work for {EPOCHS} epochs.",
        f"Peak uncapped kleos share {peak_uncapped:.1%} was cut to {peak_upper:.1%} by the "
        "per-identity weight cap (WP §10.5).",
        f"Peak decisive bicameral power (min of chambers): {peak['decisive_power']:.1%} at "
        f"epoch {peak['epoch']} — {'REACHES' if measures['blocking_minority_reached'] else 'below'} "
        "the 1/3 blocking threshold, "
        f"{'REACHES' if measures['capture_reached'] else 'below'} majority capture.",
        "The patience curve is the whitepaper's honest residue (§16): decay and caps make "
        "share a race against erosion, not a wall — the trajectory series is the deliverable.",
    ]
    write_report("s7_patience", "S7 — The patience attacker",
                 __doc__.strip().split("\n\n")[0], measures, narrative)
    return measures


if __name__ == "__main__":
    result = main()
    print({k: v for k, v in result.items() if k != "trajectory"})

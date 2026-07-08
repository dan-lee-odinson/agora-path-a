"""Milestone-3 gate: the honest-population baseline runs 26 epochs stably.

'Stably' asserted as: zero ledger-invariant violations, escrow empty at every epoch
close, sustained settlement volume (no collapse), fee rate bounded and eventually
convergent, and the activation clock actually advancing — the sim's own version of
the Launch Spec §1 empirical questions answered in the affirmative for the honest
economy.
"""

import csv

from conftest import small

from agora.model import Model


def test_honest_baseline_26_epochs_stable(baseline_cfg, tmp_path):
    cfg = baseline_cfg
    cfg["run"]["out_dir"] = str(tmp_path)
    model = Model(cfg, run_name="baseline_gate")
    summary = model.run()

    # The Adversary-finding kill criterion (DECISIONS #16): no invariant violations.
    assert summary["invariant_violations"] == []

    with open(tmp_path / "baseline_gate" / "epochs.csv", newline="", encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))
    assert len(rows) == 26

    settled = [int(r["settled"]) for r in rows]
    volumes = [float(r["settled_volume_ergs"]) for r in rows]
    fees = [float(r["fee_rate_next"]) for r in rows]
    ratios = [float(r["credit_to_volume"]) for r in rows]

    # Sustained activity: every epoch settles work; late epochs are not collapsing.
    assert all(s > 200 for s in settled)
    assert min(volumes[13:]) > 0.5 * max(volumes[:13])

    # Fee trajectory: bounded, and the last stretch sits inside the ±20% band
    # (fee convergence is a governance-activation gate, LS §9).
    assert all(0.0 <= f < 0.05 for f in fees)
    assert int(rows[-1]["fee_convergence_streak"]) >= 3

    # Supply stability (LS §10 is about *growth*, not level): the credit/volume
    # ratio must plateau, not grow superlinearly. Late-epoch relative growth of
    # credit outstanding stays small, and the ratio stays within an order-of-
    # magnitude sanity bound of its structural scale (population × floor / volume).
    credits = [float(r["credit_outstanding_ergs"]) for r in rows]
    late_growth = [(credits[i] - credits[i - 1]) / credits[i - 1] for i in range(-5, 0)]
    assert sum(late_growth) / len(late_growth) < 0.03
    assert all(r < 6.0 for r in ratios)

    # The honest economy reaches governance activation within the year.
    assert summary["activation_epoch"] > 0

    # The scheduled retarget ran at epoch 6 and chain-linked the index.
    assert len(summary["retargets"]) == 1
    assert summary["retargets"][0]["epoch"] == 6

    # Wash detection on the honest population: raw flags are the detector's
    # calibration cost (bounded), and the post-review residual — what honest
    # agents actually suffer after LS §9's Auditor review — is near zero.
    false_pos = [int(r["wash_false_pos"]) for r in rows]
    residual = [int(r["wash_fp_residual"]) for r in rows]
    total_settled = sum(settled)
    assert sum(false_pos) / total_settled < 0.05
    assert sum(residual) / total_settled < 0.01

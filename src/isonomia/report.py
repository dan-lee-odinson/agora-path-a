"""Summary report generator — renders the Sim Plan §6 metrics list plus the
Launch Spec §10 kill-criteria verdict into results/<run>/summary.md."""

from __future__ import annotations

from pathlib import Path


def _col(rows: list[dict], name: str) -> list[float]:
    return [float(r[name]) for r in rows]


def _fmt_series(values: list[float], fmt: str = "{:.3f}") -> str:
    if len(values) <= 8:
        return ", ".join(fmt.format(v) for v in values)
    head = ", ".join(fmt.format(v) for v in values[:4])
    tail = ", ".join(fmt.format(v) for v in values[-4:])
    return f"{head}, …, {tail}"


def write_summary_md(out_dir: str | Path, rows: list[dict], summary: dict) -> Path:
    """Render the per-run report. `summary` is Model.summarize()'s dict (already
    contains the kill verdict)."""
    lines = [f"# Run summary — {summary['run_name']}", ""]
    lines += [
        f"- config fingerprint `{summary['config_fingerprint']}`, seed {summary['master_seed']}, "
        f"{summary['epochs']} epochs, {summary['n_agents']} agents "
        f"({summary['n_principals']} principals)",
        f"- total settled: {summary['total_settled']} settlements, "
        f"{summary['total_settled_volume_ergs']:.0f} ergs",
        f"- defaults: {summary['total_defaults']}, socialized {summary['total_socialized_ergs']:.1f} ergs",
        f"- governance activation epoch: {summary['activation_epoch'] or 'not reached'}",
        "",
        "## Kill criteria (Launch Spec §10)",
        "",
    ]
    kill = summary["kill_criteria"]
    for name in ("supply_superlinear", "socialization_gt_5pct", "dispute_rate_gt_10pct",
                 "auditor_recall_lt_80pct", "adversary_finding"):
        verdict = kill[name]
        mark = "TRIPPED" if verdict["tripped"] else "ok"
        lines.append(f"- **{name}**: {mark} — {verdict['detail']}")
    lines.append(f"- **overall**: {'HALT AND REDESIGN' if kill['any_tripped'] else 'PASS'}")

    lines += ["", "## Epoch metrics (Sim Plan §6)", ""]
    metrics = [
        ("credit outstanding / settled volume", "credit_to_volume", "{:.3f}"),
        ("settled volume (ergs)", "settled_volume_ergs", "{:.0f}"),
        ("default socialization rate", "socialization_rate", "{:.4f}"),
        ("fee rate (next)", "fee_rate_next", "{:.4f}"),
        ("listing-price dispersion (CV)", "rate_cv", "{:.3f}"),
        ("price↔quality correlation", "price_quality_corr", "{:.3f}"),
        ("dispute rate", "dispute_rate", "{:.4f}"),
        ("qualified settlements (capped, cum.)", "qualified_capped_cum", "{:.0f}"),
        ("monoculture HHI", "monoculture_hhi", "{:.3f}"),
        ("median-agent basket pass (act.-wt.)", "median_agent_pass_est", "{:.3f}"),
        ("SCU index (difficulty shift)", "scu_index", "{:.4f}"),
        ("auditor recall", "auditor_recall", "{:.3f}"),
        ("wash flags (raw / residual FP)", "wash_flagged", "{:.0f}"),
    ]
    for label, column, fmt in metrics:
        lines.append(f"- **{label}**: {_fmt_series(_col(rows, column), fmt)}")

    lines += ["", "## Harberger markups by policy (posted rate / believed cost)", ""]
    for policy in ("honest", "overstater", "understater", "adaptive"):
        lines.append(f"- **{policy}**: {_fmt_series(_col(rows, f'markup_{policy}'), '{:.3f}')}")

    path = Path(out_dir) / "summary.md"
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path

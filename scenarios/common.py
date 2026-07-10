"""Shared infrastructure for the Sim Plan §5 attack scenarios.

Every scenario follows the same protocol:
  1. build the attack model (a Model subclass) and an unattacked TWIN with the
     same seed and baseline config — the twin is the counterfactual every
     leakage measure is computed against;
  2. run both for the same number of epochs;
  3. compute the scenario's leakage measure(s);
  4. write results/scenario_reports/<name>.md and .json.

Run any scenario directly:  python scenarios/s1_wash_rush.py
Run all seven:              python scenarios/run_all.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))

from isonomia.agents import Agent  # noqa: E402
from isonomia.config import load_config  # noqa: E402
from isonomia.model import Model  # noqa: E402
from isonomia.units import to_mergs  # noqa: E402

REPORT_DIR = REPO_ROOT / "results" / "scenario_reports"


def baseline_config(**run_overrides) -> dict:
    cfg = load_config(REPO_ROOT / "configs" / "baseline.yaml")
    cfg["run"].update(run_overrides)
    cfg.setdefault("logging", {})["events"] = False
    # Force an absolute output dir: scenarios run with scenarios/ as the CWD,
    # and the baseline's relative "results" would otherwise land there.
    cfg["run"]["out_dir"] = str(REPO_ROOT / "results")
    return cfg


def make_cohort(prefix: str, n: int, *, principals: list[str], family: int | None,
                skill: float, policy: str, cfg: dict, unit_cost_ergs: float = 17.0,
                is_poster: bool = True, families: list[int] | None = None) -> list[Agent]:
    """Deterministic adversarial cohort. `families` (cycled) overrides `family`
    when the attacker diversifies lineages."""
    cohort = []
    for i in range(n):
        fam = families[i % len(families)] if families else family
        cohort.append(Agent(
            id=f"{prefix}{i:03d}",
            principal=principals[i % len(principals)],
            family=fam,
            skill=skill,
            policy=policy,
            is_poster=is_poster,
            unit_cost_mergs=to_mergs(unit_cost_ergs),
            margin=0.15,
        ))
    return cohort


def run_twin(seed: int, epochs: int, name: str) -> Model:
    """The unattacked counterfactual: same seed, same baseline, no cohort."""
    cfg = baseline_config(master_seed=seed, epochs=epochs)
    twin = Model(cfg, run_name=name)
    twin.run()
    return twin


def series(model: Model, column: str) -> list[float]:
    return [float(r[column]) for r in model.log.epoch_rows]


def adv_settlements(model: Model, policy_prefix: str = "adv_") -> list:
    """All settlement records with an adversarial party, across the run."""
    out = []
    for epoch_settlements in model.settlements_by_epoch:
        for s in epoch_settlements:
            if (model.agents[s.poster].policy.startswith(policy_prefix)
                    or model.agents[s.worker].policy.startswith(policy_prefix)):
                out.append(s)
    return out


def write_report(name: str, title: str, description: str, measures: dict,
                 narrative: list[str]) -> Path:
    """Write the scenario report (md + json). Measures are the machine-readable
    leakage numbers; narrative is the defense-engagement trace."""
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    json_path = REPORT_DIR / f"{name}.json"
    with open(json_path, "w", encoding="utf-8", newline="\n") as fh:
        json.dump({"scenario": name, "title": title, "measures": measures},
                  fh, indent=2, sort_keys=True)
        fh.write("\n")
    md = [f"# {title}", "", description, "", "## Measures", ""]
    for key in sorted(measures):
        md.append(f"- **{key}**: {measures[key]}")
    md += ["", "## Defense engagement", ""]
    md += [f"- {line}" for line in narrative]
    md_path = REPORT_DIR / f"{name}.md"
    md_path.write_text("\n".join(md) + "\n", encoding="utf-8")
    return md_path

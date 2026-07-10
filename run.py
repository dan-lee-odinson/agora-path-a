"""Run one simulation from a config file.

Usage:
    python run.py configs/baseline.yaml
    python run.py scenarios/s1_wash_rush.yaml --seed 7 --name wash_s7

Every run is fully determined by (config file, --seed override if any); outputs land
in results/<run_name>/. See README.md.
"""

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))

from isonomia.config import load_config  # noqa: E402
from isonomia.model import Model  # noqa: E402
from isonomia.report import write_summary_md  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="ISONOMIA Path A simulation runner")
    parser.add_argument("config", help="YAML config (may use extends:)")
    parser.add_argument("--seed", type=int, default=None, help="override run.master_seed")
    parser.add_argument("--name", default=None, help="override the run name")
    parser.add_argument("--out", default=None, help="override run.out_dir")
    args = parser.parse_args()

    cfg = load_config(args.config)
    if args.seed is not None:
        cfg["run"]["master_seed"] = args.seed
    if args.out is not None:
        cfg["run"]["out_dir"] = args.out

    model = Model(cfg, run_name=args.name)
    summary = model.run()
    write_summary_md(model.log.dir, model.log.epoch_rows, summary)
    print(json.dumps({k: v for k, v in summary.items() if k != "kill_criteria"},
                     indent=2, sort_keys=True))
    kill = summary["kill_criteria"]
    print("\nkill criteria:", "HALT AND REDESIGN" if kill["any_tripped"] else "PASS")
    for name, verdict in kill.items():
        if name != "any_tripped" and verdict["tripped"]:
            print(f"  TRIPPED {name}: {verdict['detail']}")
    print(f"run complete -> {model.log.dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

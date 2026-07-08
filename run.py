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

from agora.config import load_config  # noqa: E402
from agora.model import Model  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="AGORA Path A simulation runner")
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
    print(json.dumps(summary, indent=2, sort_keys=True))
    print(f"\nrun complete -> {model.log.dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

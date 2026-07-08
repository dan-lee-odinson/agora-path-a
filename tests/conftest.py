"""Shared test fixtures."""

from pathlib import Path

import pytest

from agora.config import load_config

REPO_ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture()
def baseline_cfg() -> dict:
    """The real baseline config — tests override run size to stay fast."""
    return load_config(REPO_ROOT / "configs" / "baseline.yaml")


def small(cfg: dict, tmp_path, epochs: int = 6, n_agents: int = 60, seed: int = 42) -> dict:
    """Shrink a config for fast tests and point its output at pytest's tmp dir."""
    cfg["run"]["epochs"] = epochs
    cfg["run"]["master_seed"] = seed
    cfg["run"]["out_dir"] = str(tmp_path)
    cfg["population"]["n_agents"] = n_agents
    cfg["population"]["n_principals"] = max(10, n_agents // 4)
    cfg["economy"]["demand_tasks_per_epoch"] = max(40, n_agents * 3)
    return cfg

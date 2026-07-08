"""The discrete-epoch model loop (Sim Plan §2).

26 epochs of 14 days, seed-controlled. Milestone 1 ships the deterministic skeleton:
population synthesis, the epoch clock, per-epoch logging, and a heartbeat draw per
epoch proving substream isolation. The economic organs (ledger, escrow, listings,
fees, registry, basket, detector) are wired in at milestones 2–3.
"""

from __future__ import annotations

import hashlib
import json

from agora.agents import build_population
from agora.config import Params
from agora.rng import RngHub
from agora.runlog import RunLog


def config_fingerprint(cfg: dict) -> str:
    """Stable hash of the full config — the reproducibility identity of a run."""
    blob = json.dumps(cfg, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(blob).hexdigest()[:16]


class Model:
    def __init__(self, cfg: dict, run_name: str | None = None):
        self.cfg = cfg
        self.params = Params.from_config(cfg)
        self.n_epochs = int(cfg["run"]["epochs"])
        self.seed = int(cfg["run"]["master_seed"])
        self.hub = RngHub(self.seed)
        self.agents = build_population(cfg, self.hub)
        self.run_name = run_name or f"{cfg['meta']['name']}_s{self.seed}"
        self.log = RunLog(cfg["run"].get("out_dir", "results"), self.run_name)
        self.epoch = 0

    # ------------------------------------------------------------------ loop

    def run(self) -> dict:
        for epoch in range(1, self.n_epochs + 1):
            self.epoch = epoch
            self.step(epoch)
        summary = self.summarize()
        self.log.finalize(summary)
        return summary

    def step(self, epoch: int) -> None:
        # Heartbeat: one draw from an epoch-scoped stream. Its only job is to make
        # determinism *testable* at milestone 1 — identical seeds must reproduce it,
        # different seeds must not.
        heartbeat = self.hub.stream(f"heartbeat.e{epoch}").random()
        self.log.epoch_row(
            {
                "epoch": epoch,
                "n_agents_active": sum(1 for a in self.agents if a.active),
                "heartbeat": f"{heartbeat:.12f}",
            }
        )

    # --------------------------------------------------------------- summary

    def summarize(self) -> dict:
        families: dict[str, int] = {}
        for agent in self.agents:
            families[str(agent.family)] = families.get(str(agent.family), 0) + 1
        return {
            "run_name": self.run_name,
            "config_fingerprint": config_fingerprint(self.cfg),
            "master_seed": self.seed,
            "epochs": self.n_epochs,
            "n_agents": len(self.agents),
            "n_principals": len({a.principal for a in self.agents}),
            "family_counts": families,
            "policy_counts": {
                p: sum(1 for a in self.agents if a.policy == p)
                for p in sorted({a.policy for a in self.agents})
            },
        }

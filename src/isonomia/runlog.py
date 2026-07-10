"""Run output writer: per-epoch CSV, event-level JSONL, and summary JSON/MD.

Per the Sim Plan §7 deliverable ("seeded, config-driven, per-epoch logs"), every run
writes:
  results/<run_name>/epochs.csv    one row per epoch, fixed column order
  results/<run_name>/events.jsonl  optional event-level detail (settlements, defaults...)
  results/<run_name>/summary.json  end-of-run metrics + kill-criteria verdict
  results/<run_name>/summary.md    human-readable rendering of the same

Writers are strictly deterministic: column order is frozen by the first epoch row,
JSON is dumped with sorted keys, and no timestamps enter any artifact (timestamps
would break byte-identical reproducibility, which tests assert).
"""

from __future__ import annotations

import csv
import json
from pathlib import Path


class RunLog:
    def __init__(self, out_dir: str | Path, run_name: str, events_enabled: bool = True,
                 persist: bool = True):
        """persist=False keeps everything in memory and writes no files — used by
        the parameter sweep, where thousands of runs need only their aggregates."""
        self.dir = Path(out_dir) / run_name
        self.run_name = run_name
        self.epoch_rows: list[dict] = []
        self.persist = persist
        self.events_enabled = events_enabled and persist
        self._events_fh = None
        if persist:
            self.dir.mkdir(parents=True, exist_ok=True)
        if self.events_enabled:
            self._events_fh = open(self.dir / "events.jsonl", "w", encoding="utf-8", newline="\n")

    def epoch_row(self, row: dict) -> None:
        if self.epoch_rows and list(row.keys()) != list(self.epoch_rows[0].keys()):
            raise ValueError("epoch row keys must be identical across epochs")
        self.epoch_rows.append(row)

    def event(self, kind: str, epoch: int, **fields) -> None:
        if self._events_fh is None:
            return
        record = {"kind": kind, "epoch": epoch, **fields}
        self._events_fh.write(json.dumps(record, sort_keys=True) + "\n")

    def finalize(self, summary: dict) -> Path:
        if not self.persist:
            return self.dir
        with open(self.dir / "epochs.csv", "w", encoding="utf-8", newline="") as fh:
            if self.epoch_rows:
                writer = csv.DictWriter(fh, fieldnames=list(self.epoch_rows[0].keys()))
                writer.writeheader()
                writer.writerows(self.epoch_rows)
        if self._events_fh is not None:
            self._events_fh.close()
        with open(self.dir / "summary.json", "w", encoding="utf-8", newline="\n") as fh:
            json.dump(summary, fh, indent=2, sort_keys=True)
            fh.write("\n")
        return self.dir

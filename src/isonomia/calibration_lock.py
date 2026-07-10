"""Calibration lock: bind the derived kill-criterion floors to the code and
config they were derived from.

The v3 supply criterion's floors depend on TWO coupled subsystems: the
wash-detector parameters (they shape qualified volume, the criterion's
denominator, DECISIONS #30) and killcriteria.py itself (the statistic and floor
constants). If either changes, the floors must be re-derived
(sweep/derive_noise_floor.py) or the single source of truth silently splits.

This module computes a hash over exactly those inputs. The derivation writes the
current hash into its artifact; a CI test (tests/test_calibration_lock.py) fails
if the live hash no longer matches the artifact — forcing re-derivation whenever
the coupled subsystems change.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parents[2]
DERIVATION_ARTIFACT = REPO_ROOT / "results" / "sweep_reports" / "noise_floor_derivation.json"

# Files whose content feeds the floors. killcriteria.py holds the statistic +
# floor constants; detector params live in the baseline config's `detector` block.
_CRITERION_SRC = REPO_ROOT / "src" / "isonomia" / "killcriteria.py"
_BASELINE_CFG = REPO_ROOT / "configs" / "baseline.yaml"


def detector_config() -> dict:
    with open(_BASELINE_CFG, "r", encoding="utf-8") as fh:
        return yaml.safe_load(fh)["detector"]


def calibration_hash() -> str:
    """SHA-256 over (killcriteria.py source, detector config block). Any change to
    the criterion code or the wash-detector parameters changes this hash."""
    h = hashlib.sha256()
    h.update(_CRITERION_SRC.read_bytes())
    h.update(json.dumps(detector_config(), sort_keys=True).encode("utf-8"))
    return h.hexdigest()


def stamped_hash() -> str | None:
    """The calibration hash recorded in the derivation artifact, or None."""
    if not DERIVATION_ARTIFACT.exists():
        return None
    with open(DERIVATION_ARTIFACT, "r", encoding="utf-8") as fh:
        return json.load(fh).get("calibration_hash")

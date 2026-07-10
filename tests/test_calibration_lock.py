"""CI guard: the derived kill-criterion floors must be re-derived whenever the
coupled subsystems they depend on (wash-detector params, killcriteria code)
change. Otherwise the single source of truth silently splits (DECISIONS #33).

This test fails if the live calibration hash (over killcriteria.py + the detector
config block) does not match the hash stamped into the floor-derivation artifact.
To fix a legitimate failure: re-run `python sweep/derive_noise_floor.py`, review
the new floors/margins, update SUPPLY_FLOORS if needed, and commit the refreshed
artifact — never edit the hash by hand.
"""

import pytest

from isonomia.calibration_lock import (DERIVATION_ARTIFACT, calibration_hash,
                                    stamped_hash)


def test_floor_derivation_artifact_exists():
    assert DERIVATION_ARTIFACT.exists(), (
        "noise_floor_derivation.json missing — run sweep/derive_noise_floor.py")


def test_calibration_hash_matches_derivation_artifact():
    stamped = stamped_hash()
    assert stamped is not None, (
        "derivation artifact has no calibration_hash — re-run derive_noise_floor.py")
    live = calibration_hash()
    assert live == stamped, (
        "wash-detector config or killcriteria.py changed since the floors were "
        "derived. The supply criterion's denominator (qualified volume) depends on "
        "the detector, so the floors are stale. Re-run:\n"
        "  python sweep/derive_noise_floor.py\n"
        "review the separation table, update SUPPLY_FLOORS if the margins moved, and "
        "commit the refreshed noise_floor_derivation.json.\n"
        f"  live   = {live}\n  stamped = {stamped}")

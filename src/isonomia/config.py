"""Configuration loading and the Launch Spec §8 parameter registry.

`load_config` reads a YAML file into a plain nested dict. A config may declare
`extends: <path>` (relative to its own location) to deep-merge over a base file —
this is how the attack scenarios (Sim Plan §5) and sweep points stay small diffs
against configs/baseline.yaml rather than forks of it.

`Params` is the typed form of the Launch Spec §8 registry plus the §7 credit/fee
rules. Every simulation-tunable named in the Sim Plan §4 sweep table is a field here.
"""

from __future__ import annotations

import copy
import dataclasses
from pathlib import Path

import yaml

from isonomia.units import to_mergs


def _deep_merge(base: dict, override: dict) -> dict:
    """Recursively merge `override` into a copy of `base`. Lists replace, dicts merge."""
    merged = copy.deepcopy(base)
    for key, value in override.items():
        if isinstance(value, dict) and isinstance(merged.get(key), dict):
            merged[key] = _deep_merge(merged[key], value)
        else:
            merged[key] = copy.deepcopy(value)
    return merged


def load_config(path: str | Path) -> dict:
    """Load a YAML config, resolving at most one `extends:` chain per file."""
    path = Path(path)
    with open(path, "r", encoding="utf-8") as fh:
        cfg = yaml.safe_load(fh) or {}
    base_ref = cfg.pop("extends", None)
    if base_ref is not None:
        base = load_config((path.parent / base_ref).resolve())
        cfg = _deep_merge(base, cfg)
    return cfg


@dataclasses.dataclass(frozen=True)
class Params:
    """Launch Spec §8 parameter registry + §7 credit/fee constants, typed and validated."""

    p_star: float
    delta: float
    k_prior: float
    lambda_inherit: float
    alpha: float
    beta_listing: float
    capacity_min_tasks: int
    d_erg: float
    l_cap_mult: float
    jury_size: int
    seed_fault_rate: float
    auditor_sensitivity: float
    kleos_half_life_days: float
    duty_quota: int
    settlement_fee_init: float
    epoch_days: int
    v_window_epochs: int
    bond_duty_units: int
    l_floor_nominal_ergs: float
    withdrawal_fee: float
    listing_suspend_util: float
    retarget_epoch: int
    retire_pass_threshold: float
    w_cap_frac: float

    @classmethod
    def from_config(cls, cfg: dict) -> "Params":
        fields = {f.name for f in dataclasses.fields(cls)}
        given = cfg["params"]
        unknown = set(given) - fields
        if unknown:
            raise ValueError(f"unknown params in config: {sorted(unknown)}")
        missing = fields - set(given)
        if missing:
            raise ValueError(f"missing params in config: {sorted(missing)}")
        params = cls(**given)
        params.validate()
        return params

    def validate(self) -> None:
        checks = [
            (0.0 < self.p_star < 1.0, "p_star in (0,1)"),
            (0.0 <= self.delta < 0.5, "delta in [0,0.5)"),
            (0.0 < self.alpha <= 1.0, "alpha in (0,1]"),
            (0.0 <= self.beta_listing < 0.2, "beta_listing in [0,0.2)"),
            (self.d_erg > 0, "d_erg > 0"),
            (self.l_cap_mult >= 1.0, "l_cap_mult >= 1"),
            (self.capacity_min_tasks >= 1, "capacity_min_tasks >= 1"),
            (0.0 <= self.settlement_fee_init < 0.2, "settlement fee in [0,0.2)"),
            (self.v_window_epochs >= 1, "v_window_epochs >= 1"),
            (0.0 < self.listing_suspend_util < 1.0, "listing_suspend_util in (0,1)"),
            (0.0 <= self.withdrawal_fee < 1.0, "withdrawal_fee in [0,1)"),
            (0.0 <= self.seed_fault_rate < 1.0, "seed_fault_rate in [0,1)"),
            (0.0 <= self.auditor_sensitivity <= 1.0, "auditor_sensitivity in [0,1]"),
        ]
        for ok, rule in checks:
            if not ok:
                raise ValueError(f"parameter out of range: {rule}")

    # ---- derived quantities -------------------------------------------------

    @property
    def bond_value_mergs(self) -> int:
        """Bond collateral value: 30 duty-units × D_erg ergs each (LS §7)."""
        return to_mergs(self.bond_duty_units * self.d_erg)

    @property
    def l_floor_active_mergs(self) -> int:
        """Collateralization invariant: L_floor_active = min(200, 30 × D_erg) (LS §7).

        The active credit floor may not exceed bond collateral; if D_erg drops below
        ~6.67 the floor contracts to match — the invariant governs, not the nominal 200.
        """
        return min(to_mergs(self.l_floor_nominal_ergs), self.bond_value_mergs)

    @property
    def l_cap_mergs(self) -> int:
        """Credit hard cap = l_cap_mult × L_floor_active (LS §7/§8; DECISIONS #12)."""
        return int(self.l_cap_mult * self.l_floor_active_mergs)

    @property
    def kleos_epoch_decay(self) -> float:
        """Per-epoch kleos decay factor from the half-life in days (DECISIONS #18)."""
        return 0.5 ** (self.epoch_days / self.kleos_half_life_days)

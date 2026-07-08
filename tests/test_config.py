"""Config loading, extends-merging, and parameter validation."""

import pytest

from agora.config import Params, load_config, _deep_merge
from test_ledger import make_params


def test_extends_deep_merges_over_base(tmp_path):
    base = tmp_path / "base.yaml"
    base.write_text("a: 1\nnest: {x: 1, y: 2}\n", encoding="utf-8")
    child = tmp_path / "child.yaml"
    child.write_text("extends: base.yaml\nnest: {y: 99}\nb: 2\n", encoding="utf-8")
    cfg = load_config(child)
    assert cfg == {"a": 1, "b": 2, "nest": {"x": 1, "y": 99}}


def test_deep_merge_does_not_mutate_base():
    base = {"nest": {"x": 1}}
    _deep_merge(base, {"nest": {"x": 2}})
    assert base["nest"]["x"] == 1


def test_params_reject_unknown_and_out_of_range(baseline_cfg):
    cfg = baseline_cfg
    cfg["params"]["no_such_param"] = 1
    with pytest.raises(ValueError, match="unknown"):
        Params.from_config(cfg)
    del cfg["params"]["no_such_param"]
    cfg["params"]["alpha"] = 0.0
    with pytest.raises(ValueError, match="alpha"):
        Params.from_config(cfg)


def test_l_cap_scales_the_active_floor():
    # DECISIONS #12: the cap contracts with the collateralized floor.
    assert make_params(d_erg=8.0).l_cap_mergs == 10 * make_params(d_erg=8.0).l_floor_active_mergs
    assert make_params(d_erg=5.0).l_cap_mergs == 10 * 150_000


def test_baseline_config_params_load(baseline_cfg):
    params = Params.from_config(baseline_cfg)
    assert params.l_floor_active_mergs == 200_000
    assert params.bond_value_mergs == 240_000
    assert 0.947 < params.kleos_epoch_decay < 0.948  # 0.5^(14/180)

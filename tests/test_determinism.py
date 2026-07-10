"""Determinism is the quality bar's first line: identical config + seed must
reproduce a run byte-for-byte (Sim Plan §2)."""

from conftest import small

from isonomia.model import Model


def _run_bytes(cfg: dict, name: str, base_dir) -> tuple[bytes, bytes]:
    model = Model(cfg, run_name=name)
    model.run()
    out = base_dir / name
    return (out / "epochs.csv").read_bytes(), (out / "summary.json").read_bytes()


def test_same_seed_reproduces_byte_identical_outputs(baseline_cfg, tmp_path):
    cfg = small(baseline_cfg, tmp_path)
    csv_a, summary_a = _run_bytes(cfg, "run_a", tmp_path)
    csv_b, summary_b = _run_bytes(cfg, "run_b", tmp_path)
    # summary.json embeds run_name; compare it with the name normalized out.
    assert csv_a == csv_b
    assert summary_a.replace(b"run_a", b"X") == summary_b.replace(b"run_b", b"X")


def test_different_seed_diverges(baseline_cfg, tmp_path):
    cfg = small(baseline_cfg, tmp_path, seed=42)
    csv_a, _ = _run_bytes(cfg, "seed42", tmp_path)
    cfg2 = small(baseline_cfg, tmp_path, seed=43)
    csv_b, _ = _run_bytes(cfg2, "seed43", tmp_path)
    assert csv_a != csv_b


def test_population_is_deterministic_and_composed_as_configured(baseline_cfg, tmp_path):
    cfg = small(baseline_cfg, tmp_path, n_agents=120)
    model = Model(cfg, run_name="pop")
    counts = model.summarize()["policy_counts"]
    assert sum(counts.values()) == 120
    # Largest-remainder apportionment: every configured policy is represented and
    # honest dominates per the baseline mix.
    assert counts["honest"] == max(counts.values())
    assert set(counts) == {
        "honest", "orchestrator", "overstater", "understater", "adaptive", "marginal", "defaulter",
    }

"""WashDetector: plants known wash structures, asserts flags; asserts near-silence
on a dispersed honest graph."""

from agora.records import SettlementRecord
from agora.washdetector import WashDetector

DET_CFG = {
    "cycle_max_len": 3, "cycle_balance_ratio": 0.5, "cycle_min_share": 0.20,
    "repeat_pair_share": 0.25, "repeat_pair_min": 8,
    "trivial_size_quantile": 0.10, "trivial_rate_z": 3.0,
    "trivial_min_share": 0.50, "trivial_min_count": 5, "pass_rate_z": 3.0,
}


def rec(eid, poster, worker, quote=20_000, size=1.0, passed=True):
    return SettlementRecord(
        escrow_id=eid, epoch=1, poster=poster, worker=worker,
        poster_principal=f"pr_{poster}", worker_principal=f"pr_{worker}",
        poster_family=0, worker_family=1, template_id=0, band=0,
        size_units=size, quote=quote, passed=passed, disputed=False, seeded_fault=False,
    )


def dispersed_honest(n=120):
    """Each agent trades once with a distinct counterparty — no structure."""
    return [rec(i, f"h{i:03d}", f"w{i:03d}", size=0.8 + (i % 40) * 0.02) for i in range(n)]


def test_circular_two_cycle_flagged():
    records = dispersed_honest() + [rec(900, "X", "Y"), rec(901, "Y", "X")]
    counts = WashDetector(DET_CFG).scan(records)
    assert counts["circular"] >= 2
    assert all(s.wash_flagged for s in records if s.escrow_id in (900, 901))


def test_circular_three_cycle_flagged():
    records = dispersed_honest() + [rec(910, "X", "Y"), rec(911, "Y", "Z"), rec(912, "Z", "X")]
    WashDetector(DET_CFG).scan(records)
    assert all(s.wash_flagged for s in records if s.escrow_id in (910, 911, 912))


def test_repeat_counterparty_concentration_flagged_when_bidirectional():
    # A sustainable wash pair must recirculate value (mutual credit exhausts a
    # one-way payer's line), so the flag requires flow in both directions.
    hot = [rec(920 + i, "X", "Y") for i in range(6)] + [rec(940 + i, "Y", "X") for i in range(6)]
    records = dispersed_honest() + hot
    counts = WashDetector(DET_CFG).scan(records)
    assert counts["repeat_pair"] >= 12
    assert all(s.wash_flagged for s in hot)


def test_one_way_concentration_is_a_customer_not_wash():
    # A poster leaning on one favorite worker is normal commerce: no reverse
    # flow, no flag — this was the dominant honest-baseline false positive.
    hot = [rec(960 + i, "X", "Y") for i in range(10)]
    records = dispersed_honest() + hot
    WashDetector(DET_CFG).scan(records)
    assert not any(s.wash_flagged for s in hot)


def test_honest_dispersed_graph_is_clean():
    records = dispersed_honest()
    counts = WashDetector(DET_CFG).scan(records)
    assert counts["flagged"] == 0
    assert not any(s.wash_flagged for s in records)

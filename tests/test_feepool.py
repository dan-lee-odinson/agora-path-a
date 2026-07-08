"""FeePool: the balanced-budget retarget (LS §13.2) — never negative, listing offset,
zero-volume guard, convergence streak."""

from agora.feepool import FeePool
from agora.units import to_mergs
from test_ledger import make_ledger

COST_CFG = {"fixed_ergs": 30.0, "per_settlement_ergs": 0.15, "per_probe_ergs": 0.05}


def make_pool():
    ledger = make_ledger(2)
    return ledger, FeePool(ledger, ledger.params, COST_CFG)


def test_retarget_formula_and_listing_offset():
    _, pool = make_pool()
    row = pool.close_epoch(1, n_settlements=900, settled_volume=to_mergs(18_000),
                           n_probes=1920, socialized=0, listing_revenue=to_mergs(96))
    cost = to_mergs(30) + 900 * to_mergs(0.15) + 1920 * to_mergs(0.05)
    assert row["cost"] == cost
    expected = (cost - to_mergs(96)) / to_mergs(18_000)
    assert abs(row["fee_rate_next"] - expected) < 1e-12
    assert pool.fee_rate == row["fee_rate_next"]


def test_fee_never_negative_when_listing_revenue_exceeds_cost():
    _, pool = make_pool()
    row = pool.close_epoch(1, n_settlements=10, settled_volume=to_mergs(200),
                           n_probes=0, socialized=0, listing_revenue=to_mergs(10_000))
    assert row["fee_rate_next"] == 0.0          # max(0, ·) — the quality-bar invariant


def test_zero_volume_carries_prior_rate():
    _, pool = make_pool()
    assert pool.fee_rate == 0.01
    row = pool.close_epoch(1, n_settlements=0, settled_volume=0,
                           n_probes=100, socialized=0, listing_revenue=0)
    assert row["fee_rate_next"] == 0.01         # DECISIONS #9


def test_socialized_losses_are_an_audited_cost_line_item():
    _, pool = make_pool()
    base = pool.audited_cost(100, 100, 0)
    with_loss = pool.audited_cost(100, 100, to_mergs(50))
    assert with_loss - base == to_mergs(50)     # WP §4.5


def test_convergence_streak_tracks_20pct_band():
    _, pool = make_pool()
    volume = to_mergs(20_000)
    # Repeated identical epochs: rate settles, streak builds after the first jump.
    streaks = []
    for epoch in range(1, 6):
        row = pool.close_epoch(epoch, n_settlements=800, settled_volume=volume,
                               n_probes=1600, socialized=0, listing_revenue=to_mergs(90))
        streaks.append(row["convergence_streak"])
    # Epoch 1 jumps 1.0% → 0.7% (|Δ| = 30%, streak resets); identical epochs then
    # hold the rate exactly flat and the streak builds.
    assert streaks == [0, 1, 2, 3, 4]
    _, pool = make_pool()
    pool.close_epoch(1, 800, volume, 1600, 0, to_mergs(90))
    # A cost shock >20% resets the streak.
    pool.close_epoch(2, 800, volume, 1600, to_mergs(3000), to_mergs(90))
    assert pool.convergence_streak == 0


def test_extinguishes_only_what_the_pool_holds():
    ledger, pool = make_pool()
    ledger.fund_escrow("a00", to_mergs(100))
    ledger.settle_from_escrow("a01", to_mergs(100), to_mergs(1))  # pool holds 1 erg
    row = pool.close_epoch(1, 1, to_mergs(100), 10, 0, 0)
    assert row["extinguished"] == to_mergs(1)
    assert ledger.balance("FEEPOOL") == 0
    assert ledger.total() == 0

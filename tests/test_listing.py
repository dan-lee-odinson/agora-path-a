"""ListingMarket: β fee, suspension guard, capacity protocol, matching."""

from agora.listing import ListingMarket
from agora.units import fee_of, to_mergs
from test_ledger import make_ledger


def make_market(n_agents=4):
    ledger = make_ledger(n_agents)
    return ledger, ListingMarket(ledger, ledger.params)


def test_beta_fee_charged_on_declared_envelope():
    ledger, market = make_market()
    market.set_listing("a00", rate=to_mergs(20), capacity_tasks=5)
    revenue = market.open_epoch()
    expected = fee_of(to_mergs(20) * 5, 0.005)  # β·r·capacity (LS §7; DECISIONS #5)
    assert revenue == expected
    assert ledger.balance("a00") == -expected   # fee may draw credit (LS §13.3)
    assert ledger.balance("FEEPOOL") == expected


def test_suspension_within_10pct_of_credit_limit():
    ledger, market = make_market()
    line = ledger.credit_line("a00")
    # Drive a00 to 91% utilization, then open the epoch.
    ledger.fund_escrow("a00", int(line * 0.91))
    market.set_listing("a00", rate=to_mergs(20), capacity_tasks=5)
    market.set_listing("a01", rate=to_mergs(25), capacity_tasks=5)
    revenue = market.open_epoch()
    assert market.get("a00").suspended          # LS §13.3: capacity zero, no penalty
    assert market.headroom("a00") == 0
    assert not market.get("a01").suspended
    assert revenue == fee_of(to_mergs(25) * 5, 0.005)  # only a01 paid


def test_capacity_below_minimum_delists():
    _, market = make_market()
    market.set_listing("a00", rate=to_mergs(20), capacity_tasks=0)
    assert market.get("a00") is None            # LS §7: capacity_min enforced


def test_consume_at_funding_and_restore():
    _, market = make_market()
    market.set_listing("a00", rate=to_mergs(20), capacity_tasks=2)
    market.open_epoch()
    envelope = market.get("a00").envelope
    assert market.consume("a00", envelope)      # fill the whole envelope
    assert market.headroom("a00") == 0
    assert not market.consume("a00", 1)         # over-envelope refused
    market.restore("a00", envelope)             # withdrawal/invalidation path
    assert market.headroom("a00") == envelope


def test_matching_prefers_quality_adjusted_rate_and_respects_bands():
    from agora.agents import Agent

    _, market = make_market()

    def agent(aid, band, delivered):
        a = Agent(id=aid, principal="P0", family=0, skill=0.0, policy="honest",
                  is_poster=False, unit_cost_mergs=to_mergs(17), margin=0.15)
        a.max_band = band
        a.exam_score = delivered
        return a

    agents = {"a00": agent("a00", band=2, delivered=0.9),
              "a01": agent("a01", band=2, delivered=0.3),
              "a02": agent("a02", band=0, delivered=0.9)}
    market.set_listing("a00", rate=to_mergs(24), capacity_tasks=5)  # pricier but good
    market.set_listing("a01", rate=to_mergs(20), capacity_tasks=5)  # cheap but bad
    market.set_listing("a02", rate=to_mergs(10), capacity_tasks=5)  # cheapest, band-ineligible
    market.open_epoch()
    quality = lambda a: max(0.05, a.exam_score)  # noqa: E731
    # Band-2 task: a02 excluded by band; 24/0.9 = 26.7 beats 20/0.3 = 66.7.
    assert market.cheapest_eligible(1.0, band=2, agents=agents, exclude="x", quality_of=quality) == "a00"
    # Raw-cheapest (no quality signal) would pick a01.
    assert market.cheapest_eligible(1.0, band=2, agents=agents, exclude="x") == "a01"
    # Band-0 task: the cheap small model wins — full citizen in its band (LS §5.1).
    assert market.cheapest_eligible(1.0, band=0, agents=agents, exclude="x", quality_of=quality) == "a02"

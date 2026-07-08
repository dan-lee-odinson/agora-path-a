"""Basket: p* calibration, exam banding, the epoch-6 retarget, SCU chain-link."""

from agora.agents import Agent
from agora.basket import Basket
from agora.rng import RngHub


def make_agent(aid="a0000", skill=0.0, family=0):
    return Agent(id=aid, principal="P0", family=family, skill=skill, policy="honest",
                 is_poster=False, unit_cost_mergs=17_000, margin=0.15)


def make_basket(cfg_overrides=None, median_skill=0.0):
    cfg = {
        "population": {"lineage_families": 4, "family_template_affinity_sd": 0.4},
        "basket": {
            "n_templates": 600, "n_reserve_templates": 120, "difficulty_sd": 0.9,
            "pass_slope": 1.5, "n_bands": 3, "exam_tasks": 40,
            "band_eligibility_min_pass": 0.35,
        },
    }
    if cfg_overrides:
        cfg["basket"].update(cfg_overrides)
    return Basket(cfg, RngHub(7), median_skill)


def test_median_agent_pass_rate_targets_p_star():
    """LS §5.3: difficulty spread targets median-agent pass rate p* = 0.5. The
    logistic is symmetric around the median skill, so the median agent's expected
    pass over the basket must sit near 0.5 (affinity noise averages out)."""
    basket = make_basket(median_skill=0.3)
    median_agent = make_agent(skill=0.3)
    assert abs(basket.agent_mean_pass(median_agent) - 0.5) < 0.04
    # Skill monotonicity: stronger agents pass more.
    assert basket.agent_mean_pass(make_agent(skill=1.5)) > 0.7
    assert basket.agent_mean_pass(make_agent(skill=-1.5)) < 0.3


def test_exam_scores_and_bands_track_skill():
    basket = make_basket()
    weak, strong = make_agent("a0001", skill=-2.0), make_agent("a0002", skill=2.0)
    basket.examine(weak)
    basket.examine(strong)
    assert strong.exam_score > weak.exam_score
    assert strong.max_band >= weak.max_band
    assert weak.max_band >= 0                      # band 0 is citizenship (LS §5.1)


def test_retarget_retires_saturated_templates_and_chain_links():
    basket = make_basket()
    strong = make_agent(skill=3.0)
    # Saturate the 50 easiest templates with a strong agent's outcomes.
    easiest = sorted(basket.active_templates(), key=lambda t: t.difficulty)[:50]
    rng = RngHub(9).stream("t")
    for template in easiest:
        for _ in range(12):
            basket.record_outcome(template.id, rng.random() < basket.pass_prob(strong, template))
    before_difficulty = basket.mean_active_difficulty()
    result = basket.retarget(epoch=6, retire_threshold=0.60)
    assert result["retired"] > 0
    assert result["admitted"] == result["retired"]  # reserve refills the basket
    assert len(basket.active_templates()) == 600
    assert basket.mean_active_difficulty() > before_difficulty  # frontier admitted
    assert result["scu_index"] == basket.scu_index
    assert basket.scu_index != 1.0                  # chain-linked movement recorded


def test_templates_without_evidence_are_not_retired():
    basket = make_basket()
    result = basket.retarget(epoch=6, retire_threshold=0.60)  # no outcomes recorded
    assert result["retired"] == 0
    assert result["admitted"] == 0
    assert basket.scu_index == 1.0


def test_template_lookup_stable_across_retarget():
    basket = make_basket()
    strong = make_agent(skill=3.0)
    for template in sorted(basket.active_templates(), key=lambda t: t.difficulty)[:30]:
        for _ in range(10):
            basket.record_outcome(template.id, True)
    basket.retarget(epoch=6, retire_threshold=0.60)
    for template in basket.active_templates():
        assert basket.template(template.id).id == template.id

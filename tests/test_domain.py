from __future__ import annotations

from quant_research_os.domain import (
    Alpha,
    AlphaStatus,
    Experiment,
    ResearchPlan,
    ResearchRequest,
    Strategy,
)


def test_research_request_defaults():
    req = ResearchRequest(
        user_question="Find a robust cross-sectional FX strategy with low momentum correlation."
    )
    assert req.research_id.startswith("RES-")
    assert req.budget.max_experiments == 50
    assert req.status.value == "CREATED"


def test_research_plan_roundtrip():
    plan = ResearchPlan(
        research_id="RES-abc",
        research_question="FX diversification",
        economic_hypothesis="Carry may diversify momentum",
        success_criteria=["OOS Sharpe > 0.5", "corr(momentum) < 0.3"],
        failure_criteria=["Fails pessimistic costs"],
    )
    data = plan.model_dump()
    restored = ResearchPlan.model_validate(data)
    assert restored.economic_hypothesis.startswith("Carry")


def test_experiment_and_alpha_lifecycle_fields():
    exp = Experiment(research_id="RES-1", strategy_id="STR-1", random_seed=7)
    assert exp.status.value == "PENDING"
    alpha = Alpha(
        strategy_id="STR-1",
        hypothesis="carry",
        expected_economic_mechanism="interest rate differential",
        universe="FX_G10",
        status=AlphaStatus.PROPOSED,
    )
    assert alpha.metrics == {}
    assert alpha.metrics_source_ids == []


def test_strategy_versioning_fields():
    s1 = Strategy(
        name="cs_carry",
        description="cross-sectional carry",
        economic_rationale="high yield currencies appreciate on average",
        universe="FX_G10",
        signal_definition="rank(carry)",
        version="1",
    )
    s2 = s1.model_copy(update={"version": "2", "parent_strategy_id": s1.strategy_id})
    assert s2.parent_strategy_id == s1.strategy_id
    assert s2.version == "2"

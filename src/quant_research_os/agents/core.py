"""Deterministic research agents — structured outputs; tools for all numbers."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

from quant_research_os.domain.enums import ResearchDecision, Severity
from quant_research_os.domain.research import CandidateHypothesis, ResearchPlan, ResearchRequest
from quant_research_os.domain.review import ReviewFinding, ReviewResult
from quant_research_os.domain.strategy import Strategy
from quant_research_os.tools.router import ToolRouter


class AgentDecision(BaseModel):
    decision: str
    confidence: float = 0.5
    reasoning_summary: str = ""
    findings: list[str] = Field(default_factory=list)
    required_experiments: list[dict[str, Any]] = Field(default_factory=list)
    risks: list[str] = Field(default_factory=list)
    payload: dict[str, Any] = Field(default_factory=dict)


def plan_research(request: ResearchRequest) -> ResearchPlan:
    q = request.user_question.lower()
    universe = request.universe or ("FX_G10" if "fx" in q else "UNKNOWN")
    hypotheses = [
        CandidateHypothesis(
            name="cross_sectional_carry",
            economic_intuition="High-yield currencies earn carry; may diversify momentum.",
            expected_direction="long high carry / short low carry",
            expected_horizon="weeks to months",
            required_features=["carry"],
            implementation_approach="rank carry proxy cross-sectionally",
            falsification_criteria="OOS Sharpe<=0 after costs or corr(momentum)>0.5",
            rationale="Classic FX premium distinct from trend following",
        ),
        CandidateHypothesis(
            name="short_term_reversal",
            economic_intuition="Transitory flows reverse over short horizons.",
            expected_direction="long losers / short winners (short lookback)",
            expected_horizon="days to weeks",
            required_features=["reversal"],
            implementation_approach="rank negative short-term returns",
            falsification_criteria="Fails walk-forward or excessive turnover under costs",
            rationale="Economically distinct from momentum",
        ),
        CandidateHypothesis(
            name="volatility_ranked",
            economic_intuition="Relative vol may forecast risk-adjusted opportunity sets.",
            expected_direction="prefer lower/higher vol basket per specification",
            expected_horizon="weeks",
            required_features=["volatility"],
            implementation_approach="rank inverse volatility / vol differentials",
            falsification_criteria="No OOS edge; pure risk packaging without alpha",
            rationale="Risk-based alternative to momentum",
        ),
        CandidateHypothesis(
            name="value_proxy",
            economic_intuition="Mean-reversion to longer-run fair value.",
            expected_direction="long cheap vs MA / short rich",
            expected_horizon="months",
            required_features=["value"],
            implementation_approach="rank distance to long MA",
            falsification_criteria="Collapses to slow momentum/reversal with high corr",
            rationale="Value-like mechanism",
        ),
        CandidateHypothesis(
            name="liquidity_stability",
            economic_intuition="More stable/liquid names earn premium in stress.",
            expected_direction="long high liquidity-proxy",
            expected_horizon="weeks to months",
            required_features=["liquidity"],
            implementation_approach="rank inverse realized vol as liquidity proxy",
            falsification_criteria="Indistinguishable from low-vol factor; no diversification",
            rationale="Liquidity channel",
        ),
    ]
    return ResearchPlan(
        research_id=request.research_id,
        research_question=request.user_question,
        economic_hypothesis=(
            "Seek cross-sectional FX alpha with low correlation to existing momentum books."
        ),
        candidate_hypotheses=hypotheses,
        required_datasets=["fx_synthetic_momentum"],
        candidate_features=["carry", "reversal", "volatility", "value", "liquidity"],
        candidate_strategies=[h.name for h in hypotheses],
        validation_plan=[
            "transaction costs baseline+pessimistic",
            "walk-forward expanding windows",
            "parameter robustness on lookback",
            "bootstrap Sharpe CIs",
            "regime conditional performance",
            "correlation vs existing momentum",
        ],
        robustness_plan=["lookback surface", "cost stress", "adversarial review"],
        success_criteria=[
            "OOS Sharpe > 0.3 after baseline costs",
            "|corr(momentum)| < 0.35",
            "parameter surface not fragile",
            "adversarial severity < CRITICAL",
        ],
        failure_criteria=[
            "Fails pessimistic costs",
            "Walk-forward mostly unprofitable",
            "High momentum correlation",
            "Adversarial CRITICAL findings",
        ],
        budget_allocation={
            "hypotheses": len(hypotheses),
            "implementations": min(20, request.budget.max_experiments // 2),
            "robustness_tests": 10,
            "adversarial_tests": 5,
        },
    )


def adversarial_review(
    *,
    candidate: dict[str, Any],
    backtest_metrics: dict[str, Any],
    walk_forward: dict[str, Any] | None,
    robustness: dict[str, Any] | None,
    stats: dict[str, Any] | None,
    diversification: dict[str, Any] | None,
    n_trials: int,
) -> ReviewResult:
    findings: list[ReviewFinding] = []

    sharpe = (backtest_metrics or {}).get("sharpe", 0.0) or 0.0
    turnover = (backtest_metrics or {}).get("turnover", 0.0) or 0.0
    mdd = (backtest_metrics or {}).get("max_drawdown", 0.0) or 0.0

    if turnover > 0.45:
        findings.append(
            ReviewFinding(
                severity=Severity.HIGH,
                category="trading",
                summary="Excessive turnover",
                detail=f"avg turnover={turnover:.3f}",
                recommended_followup="Slow rebalance frequency",
            )
        )
    elif turnover > 0.2:
        findings.append(
            ReviewFinding(
                severity=Severity.MEDIUM,
                category="trading",
                summary="Elevated turnover — cost sensitivity likely",
                detail=f"avg turnover={turnover:.3f}",
                recommended_followup="Confirm survival under pessimistic costs",
            )
        )
    if sharpe > 1.5:
        findings.append(
            ReviewFinding(
                severity=Severity.MEDIUM,
                category="statistical",
                summary="Unusually high in-sample Sharpe — suspect overfit",
                recommended_followup="Emphasize OOS/walk-forward and deflated Sharpe",
            )
        )
    if walk_forward:
        pct = (walk_forward.get("aggregate") or {}).get("pct_profitable_windows", 0)
        if pct < 0.4:
            findings.append(
                ReviewFinding(
                    severity=Severity.HIGH,
                    category="temporal",
                    summary="Walk-forward mostly unprofitable",
                    detail=f"pct_profitable_windows={pct}",
                )
            )
        oos = (walk_forward.get("aggregate") or {}).get("oos_metrics") or {}
        if oos.get("sharpe", 0) < 0.2 and sharpe > 0.5:
            findings.append(
                ReviewFinding(
                    severity=Severity.CRITICAL,
                    category="statistical",
                    summary="Severe IS/OOS degradation",
                    detail=f"IS sharpe~{sharpe:.2f} vs OOS {oos.get('sharpe')}",
                )
            )
    if robustness and robustness.get("fragile"):
        findings.append(
            ReviewFinding(
                severity=Severity.HIGH,
                category="parameter",
                summary="Fragile parameter peak",
                detail="; ".join(robustness.get("notes") or []),
            )
        )
    if stats and stats.get("multiple_testing_warning"):
        findings.append(
            ReviewFinding(
                severity=Severity.MEDIUM,
                category="statistical",
                summary="Multiple testing concern",
                detail=f"n_trials={n_trials}",
            )
        )
    if diversification and diversification.get("max_correlation") is not None:
        if abs(diversification["max_correlation"]) > 0.5:
            findings.append(
                ReviewFinding(
                    severity=Severity.HIGH,
                    category="economic",
                    summary="High correlation with existing alphas",
                    detail=f"max_|corr|={diversification['max_correlation']}",
                )
            )
        elif not diversification.get("genuine_diversification", True):
            findings.append(
                ReviewFinding(
                    severity=Severity.MEDIUM,
                    category="economic",
                    summary="Low return corr but weak genuine diversification signals",
                )
            )
    if mdd < -0.2:
        findings.append(
            ReviewFinding(
                severity=Severity.MEDIUM,
                category="trading",
                summary="Large historical drawdown",
                detail=f"max_drawdown={mdd}",
            )
        )
    if not findings:
        findings.append(
            ReviewFinding(
                severity=Severity.LOW,
                category="process",
                summary="No critical red flags under current tests",
                detail="Absence of flags is not proof of robustness",
            )
        )

    sev_order = [Severity.LOW, Severity.MEDIUM, Severity.HIGH, Severity.CRITICAL]
    worst = max(findings, key=lambda f: sev_order.index(f.severity)).severity
    if worst == Severity.CRITICAL:
        decision = ResearchDecision.REJECT
    elif worst == Severity.HIGH:
        decision = ResearchDecision.REQUIRES_MORE_RESEARCH
    elif sharpe > 0.3:
        decision = ResearchDecision.PROMISING
    else:
        decision = ResearchDecision.INCONCLUSIVE

    return ReviewResult(
        reviewer_id="adversarial_quant_v1",
        findings=findings,
        severity=worst,
        suspected_biases=[f.category for f in findings if f.severity in {Severity.HIGH, Severity.CRITICAL}],
        failed_tests=[f.summary for f in findings if f.severity in {Severity.HIGH, Severity.CRITICAL}],
        recommended_followups=[f.recommended_followup for f in findings if f.recommended_followup],
        decision=decision,
        confidence=0.55,
        reasoning_summary="Deterministic adversarial checklist over tool outputs.",
    )


SIGNAL_MAP = {
    "cross_sectional_carry": "carry",
    "short_term_reversal": "reversal",
    "volatility_ranked": "volatility",
    "value_proxy": "value",
    "liquidity_stability": "liquidity",
}


# Map feature names used as cross_sectional signal_name — engine supports momentum|reversal;
# for others we encode via signal_name extensions.
ENGINE_SIGNAL = {
    "carry": "momentum",  # slow momentum as carry proxy in price-only world — documented
    "reversal": "reversal",
    "volatility": "momentum",
    "value": "reversal",
    "liquidity": "momentum",
    "momentum": "momentum",
}

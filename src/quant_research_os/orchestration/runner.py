"""Explicit research state-machine orchestrator (no unbounded LLM loops)."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

from quant_research_os.agents.core import SIGNAL_MAP, adversarial_review, plan_research
from quant_research_os.domain.enums import AlphaStatus, ResearchDecision, ResearchStatus, Severity
from quant_research_os.domain.research import ResearchRequest
from quant_research_os.domain.strategy import Strategy
from quant_research_os.experiments.hashing import code_commit
from quant_research_os.orchestration.budget import BudgetTracker
from quant_research_os.reporting.report import ResearchReport, build_report
from quant_research_os.storage.db import ResearchDB
from quant_research_os.tools.router import ToolContext, ToolRouter


TRANSITIONS = [
    "START",
    "ResearchPlanner",
    "DataDiscovery",
    "HypothesisGeneration",
    "ExperimentDesign",
    "ExperimentExecution",
    "StatisticalValidation",
    "RobustnessTesting",
    "RegimeAnalysis",
    "DiversificationAnalysis",
    "AdversarialReview",
    "PortfolioAnalysis",
    "RiskReview",
    "PaperTradingGate",
    "Report",
    "END",
]


@dataclass
class ResearchState:
    request: ResearchRequest
    plan: dict[str, Any] = field(default_factory=dict)
    node: str = "START"
    dataset_id: str = "fx_synthetic_momentum"
    candidates: list[dict[str, Any]] = field(default_factory=list)
    reviews: list[dict[str, Any]] = field(default_factory=list)
    portfolio: dict[str, Any] | None = None
    risk: dict[str, Any] | None = None
    data_section: dict[str, Any] = field(default_factory=dict)
    decision: ResearchDecision = ResearchDecision.INCONCLUSIVE
    report: ResearchReport | None = None
    transition_log: list[dict[str, str]] = field(default_factory=list)


class ResearchOrchestrator:
    """Autonomous research laboratory runner."""

    def __init__(self, db: ResearchDB | None = None) -> None:
        self.db = db or ResearchDB()

    def _transition(self, state: ResearchState, to: str, reason: str) -> None:
        state.transition_log.append({"from": state.node, "to": to, "reason": reason})
        state.node = to
        self.db.add_trace(
            state.request.research_id,
            "orchestrator",
            "transition",
            {"to": to, "reason": reason},
        )

    def run(
        self,
        question: str,
        *,
        universe: str | None = None,
        max_experiments: int = 30,
        max_hypotheses: int | None = None,
    ) -> ResearchReport:
        request = ResearchRequest(user_question=question, universe=universe)
        request.budget.max_experiments = max_experiments
        request.status = ResearchStatus.RUNNING
        self.db.upsert_json(
            "research_requests",
            "research_id",
            request.research_id,
            request.model_dump(mode="json"),
            status=request.status.value,
            created_at=request.created_at.isoformat(),
        )
        try:
            return self._run_inner(request, max_experiments=max_experiments, max_hypotheses=max_hypotheses)
        except Exception as exc:
            request.status = ResearchStatus.FAILED
            payload = request.model_dump(mode="json")
            payload["error"] = str(exc)
            self.db.upsert_json(
                "research_requests",
                "research_id",
                request.research_id,
                payload,
                status=ResearchStatus.FAILED.value,
                created_at=request.created_at.isoformat(),
            )
            self.db.add_trace(
                request.research_id,
                "orchestrator",
                "failed",
                {"error": str(exc)},
            )
            raise

    def _run_inner(
        self,
        request: ResearchRequest,
        *,
        max_experiments: int,
        max_hypotheses: int | None,
    ) -> ResearchReport:
        budget = BudgetTracker(max_experiments=max_experiments, max_llm_calls=request.budget.max_llm_calls)
        ctx = ToolContext(self.db, research_id=request.research_id)
        tools = ToolRouter(ctx)
        state = ResearchState(request=request)

        # --- ResearchPlanner ---
        plan = plan_research(request)
        if max_hypotheses is not None:
            plan.candidate_hypotheses = plan.candidate_hypotheses[:max_hypotheses]
        state.plan = plan.model_dump(mode="json")
        self.db.upsert_json(
            "research_plans",
            "research_id",
            request.research_id,
            state.plan,
            created_at=datetime.now(timezone.utc).isoformat(),
        )
        for h in plan.candidate_hypotheses:
            self.db.upsert_json(
                "hypotheses",
                "hypothesis_id",
                h.hypothesis_id,
                h.model_dump(mode="json"),
                research_id=request.research_id,
            )
            self.db.add_edge("research", request.research_id, "has_hypothesis", "hypothesis", h.hypothesis_id)
        budget.hypotheses_generated = len(plan.candidate_hypotheses)
        self._transition(state, "ResearchPlanner", "structured plan from research question")
        self.db.save_checkpoint(request.research_id, state.node, {"budget": budget.snapshot()})

        # --- DataDiscovery ---
        ds = tools.call("list_datasets")
        # Prefer synthetic momentum FX for flagship; validate quality
        state.dataset_id = "fx_synthetic_momentum"
        val = tools.call("validate_dataset", dataset_id=state.dataset_id)
        if val.data.get("overall") == "BLOCK":
            raise RuntimeError(f"dataset blocked by quality checks: {val.data}")
        # Also validate mean-reversion panel for reversal/value hypotheses
        val_mr = tools.call("validate_dataset", dataset_id="fx_synthetic_meanrev")
        seed = tools.call("seed_momentum_baseline", dataset_id=state.dataset_id)
        existing = tools.call("analyze_existing_alpha_library")
        state.data_section = {
            "datasets": ds.data,
            "quality": val.data,
            "quality_meanrev": val_mr.data,
            "existing_library": existing.data,
            "momentum_seed": seed.data.get("alpha", {}).get("alpha_id"),
        }
        self._transition(state, "DataDiscovery", "validated FX dataset + seeded momentum library")

        # --- HypothesisGeneration (already in plan) ---
        self._transition(state, "HypothesisGeneration", "competing economic hypotheses prepared")

        # --- Experiment loop per hypothesis ---
        self._transition(state, "ExperimentDesign", "map hypotheses to CS strategies")
        lookbacks = {"carry": 60, "reversal": 1, "volatility": 20, "value": 20, "liquidity": 20, "momentum": 20}
        rebalance_for = {"carry": 5, "reversal": 1, "volatility": 5, "value": 5, "liquidity": 5, "momentum": 5}
        dataset_for_feature = {
            "carry": "fx_synthetic_momentum",
            "reversal": "fx_synthetic_meanrev",
            "volatility": "fx_synthetic_momentum",
            "value": "fx_synthetic_meanrev",
            "liquidity": "fx_synthetic_momentum",
            "momentum": "fx_synthetic_momentum",
        }

        for hyp in plan.candidate_hypotheses:
            if self.db.is_cancelled(request.research_id):
                request.status = ResearchStatus.CANCELLED
                self.db.upsert_json(
                    "research_requests",
                    "research_id",
                    request.research_id,
                    request.model_dump(mode="json"),
                    status=ResearchStatus.CANCELLED.value,
                    created_at=request.created_at.isoformat(),
                )
                break
            if not budget.can_run_experiment():
                break
            feature = SIGNAL_MAP.get(hyp.name, "momentum")
            lookback = lookbacks.get(feature, 20)
            rebalance_every = rebalance_for.get(feature, 5)
            dataset_id = dataset_for_feature.get(feature, state.dataset_id)
            alpha_id = None
            strategy = Strategy(
                name=hyp.name,
                description=hyp.economic_intuition,
                economic_rationale=hyp.rationale or hyp.economic_intuition,
                universe=request.universe or "FX_G10",
                features=[feature],
                signal_definition=f"rank({feature})",
                parameters={"lookback": lookback, "signal": feature, "rebalance_every": rebalance_every},
            )
            ctx.alphas.save_strategy(strategy)
            self.db.add_edge("hypothesis", hyp.hypothesis_id, "implements", "strategy", strategy.strategy_id)

            budget.consume_experiment()
            exp = tools.call(
                "create_experiment",
                research_id=request.research_id,
                strategy_id=strategy.strategy_id,
                hypothesis_id=hyp.hypothesis_id,
                dataset_id=dataset_id,
                parameters={"signal": feature, "lookback": lookback, "dataset_id": dataset_id},
                transaction_cost_model="baseline",
            )
            self._transition(state, "ExperimentExecution", f"backtest {hyp.name}")

            bt = tools.call(
                "run_backtest",
                dataset_id=dataset_id,
                signal_name=feature,
                lookback=lookback,
                rebalance_every=rebalance_every,
                cost_assumption="baseline",
                experiment_id=exp.data["experiment_id"],
                strategy_id=strategy.strategy_id,
            )
            if not bt.ok:
                budget.candidates_rejected += 1
                state.candidates.append(
                    {
                        "name": hyp.name,
                        "status": "REJECTED",
                        "reason": bt.error,
                        "hypothesis_id": hyp.hypothesis_id,
                    }
                )
                continue

            returns = bt.data["returns"]
            metrics = bt.data["metrics"]

            # Pessimistic cost check
            bt_pes = tools.call(
                "run_backtest",
                dataset_id=dataset_id,
                signal_name=feature,
                lookback=lookback,
                rebalance_every=rebalance_every,
                cost_assumption="pessimistic",
                strategy_id=strategy.strategy_id,
            )
            if budget.can_run_experiment():
                budget.consume_experiment()

            self._transition(state, "StatisticalValidation", f"bootstrap {hyp.name}")
            stats = tools.call(
                "run_bootstrap",
                returns=returns,
                n_trials_tested=max(budget.hypotheses_generated, budget.experiments_used),
            )

            self._transition(state, "RobustnessTesting", f"parameter surface {hyp.name}")
            rob = tools.call(
                "run_robustness_analysis",
                dataset_id=dataset_id,
                signal_name=feature,
                parameter_name="lookback",
                rebalance_every=rebalance_every,
                values=[1, 2, 3, 5] if feature == "reversal" else [max(5, lookback - 10), lookback, lookback + 10, lookback + 20],
            )

            wf = tools.call(
                "run_walk_forward",
                dataset_id=dataset_id,
                signal_name=feature,
                lookback=lookback,
                rebalance_every=rebalance_every,
                mode="expanding_window",
                cost_assumption="baseline",
            )

            self._transition(state, "RegimeAnalysis", f"regimes {hyp.name}")
            regimes = tools.call("analyze_regimes", returns=returns)

            self._transition(state, "DiversificationAnalysis", f"corr vs momentum {hyp.name}")
            div = tools.call("analyze_diversification", candidate_returns=returns)

            self._transition(state, "AdversarialReview", f"attack {hyp.name}")
            review = adversarial_review(
                candidate={"name": hyp.name},
                backtest_metrics=metrics,
                walk_forward=wf.data if wf.ok else None,
                robustness=rob.data if rob.ok else None,
                stats=stats.data if stats.ok else None,
                diversification=div.data if div.ok else None,
                n_trials=budget.experiments_used,
            )
            self.db.upsert_json("reviews", "review_id", review.review_id, review.model_dump(mode="json"))
            state.reviews.append(review.model_dump(mode="json"))

            oos_sharpe = ((wf.data.get("aggregate") or {}).get("oos_metrics") or {}).get("sharpe", 0.0) if wf.ok else 0.0
            pes_sharpe = (bt_pes.data.get("metrics") or {}).get("sharpe", 0.0) if bt_pes.ok else -999
            corr_ok = bool(div.ok and div.data.get("genuine_diversification"))
            max_corr = abs(div.data.get("max_correlation") or 0) if div.ok else 1.0
            pct_prof = ((wf.data.get("aggregate") or {}).get("pct_profitable_windows") or 0.0) if wf.ok else 0.0

            status = "REJECTED"
            reason = review.decision.value
            severity_ok = review.severity in {Severity.LOW, Severity.MEDIUM} or (
                review.severity == Severity.HIGH
                and review.decision == ResearchDecision.REQUIRES_MORE_RESEARCH
                and metrics.get("sharpe", 0) > 0.5
            )
            if review.decision == ResearchDecision.REJECT or review.severity == Severity.CRITICAL:
                status = "REJECTED"
                budget.candidates_rejected += 1
            elif (
                severity_ok
                and oos_sharpe >= 0.15
                and pct_prof >= 0.35
                and pes_sharpe > -2.0
                and metrics.get("sharpe", 0) > 0.3
                and max_corr < 0.5
                and not (rob.data or {}).get("fragile", False)
            ):
                status = "PROMISING" if (oos_sharpe < 0.8 or review.severity != Severity.LOW) else "ROBUST"
                if status == "PROMISING":
                    budget.candidates_promising += 1
                else:
                    budget.candidates_robust += 1
                saved = tools.call(
                    "save_alpha",
                    strategy_id=strategy.strategy_id,
                    hypothesis=hyp.name,
                    mechanism=hyp.economic_intuition,
                    universe=request.universe or "FX_G10",
                    features=[feature],
                    metrics=metrics,
                    metrics_source_ids=[bt.data["backtest_id"]],
                    returns=returns,
                    status=status,
                    extras={
                        "walk_forward": wf.data.get("aggregate") if wf.ok else {},
                        "robustness": rob.data if rob.ok else {},
                        "stats": {k: stats.data.get(k) for k in ("sharpe", "sharpe_ci_low", "sharpe_ci_high", "mean_return_pvalue", "notes", "deflated_sharpe_approx", "n_trials_tested")} if stats.ok else {},
                        "diversification": div.data if div.ok else {},
                        "regimes": (regimes.data if regimes.ok else {}),
                        "pessimistic_sharpe": pes_sharpe,
                    },
                )
                alpha_id = saved.data.get("alpha_id") if saved.ok else None
            else:
                status = "REJECTED"
                budget.candidates_rejected += 1
                reason = (
                    f"gates failed: oos_sharpe={oos_sharpe}, pes_sharpe={pes_sharpe}, "
                    f"max_corr={max_corr}, review={review.decision.value}"
                )

            state.candidates.append(
                {
                    "name": hyp.name,
                    "hypothesis_id": hyp.hypothesis_id,
                    "strategy_id": strategy.strategy_id,
                    "status": status,
                    "reason": reason,
                    "metrics": metrics,
                    "oos_sharpe": oos_sharpe,
                    "pessimistic_sharpe": pes_sharpe,
                    "diversification": div.data if div.ok else {},
                    "review_severity": review.severity.value,
                    "backtest_id": bt.data.get("backtest_id"),
                    "alpha_id": alpha_id,
                }
            )

        # --- Portfolio + Risk on survivors ---
        survivors = [c for c in state.candidates if c.get("status") in {"PROMISING", "ROBUST"}]
        if survivors:
            self._transition(state, "PortfolioAnalysis", "allocate across surviving alphas")
            returns_by = {}
            for c in survivors:
                # pull returns from alpha robustness
                if c.get("alpha_id"):
                    a = ctx.alphas.get(c["alpha_id"])
                    if a and a.robustness.get("returns"):
                        returns_by[c["name"]] = a.robustness["returns"]
            if returns_by:
                # include momentum baseline if present
                for a in ctx.alphas.list():
                    if a.robustness.get("seed") and a.robustness.get("returns"):
                        returns_by["existing_momentum"] = a.robustness["returns"]
                        break
                port = tools.call("optimize_portfolio", returns_by_alpha=returns_by, method="risk_parity")
                state.portfolio = port.data if port.ok else None

            self._transition(state, "RiskReview", "stress test best candidate")
            best = max(survivors, key=lambda c: c.get("oos_sharpe") or -999)
            best_alpha = ctx.alphas.get(best["alpha_id"]) if best.get("alpha_id") else None
            if best_alpha and best_alpha.robustness.get("returns"):
                stress = tools.call("run_stress_test", returns=best_alpha.robustness["returns"])
                rejects = [s for s in (stress.data.get("scenarios") or []) if s.get("decision") == "REJECT"]
                state.risk = stress.data if stress.ok else None
                if rejects:
                    # Risk veto
                    ctx.alphas.reject(best_alpha.alpha_id, "risk stress veto")
                    best["status"] = "REJECTED"
                    best["reason"] = "RISK_VETO"
                    budget.candidates_rejected += 1
                    if budget.candidates_promising:
                        budget.candidates_promising -= 1
                    survivors = [c for c in state.candidates if c.get("status") in {"PROMISING", "ROBUST"}]

            self._transition(state, "PaperTradingGate", "recommend paper if robust")
            for c in survivors:
                if c.get("status") == "ROBUST" and c.get("alpha_id"):
                    from quant_research_os.paper.engine import start_paper_trading

                    start_paper_trading(self.db, c["alpha_id"])
                    ctx.alphas.set_status(c["alpha_id"], AlphaStatus.PAPER_TRADING)
                    c["status"] = "PAPER_TRADING"

        # --- Final decision ---
        survivors = [c for c in state.candidates if c.get("status") in {"PROMISING", "ROBUST", "PAPER_TRADING"}]
        if any(c.get("status") == "PAPER_TRADING" for c in survivors):
            state.decision = ResearchDecision.ROBUST
        elif survivors:
            state.decision = ResearchDecision.PROMISING
        elif state.candidates:
            state.decision = ResearchDecision.NO_ROBUST_ALPHA_FOUND
        else:
            state.decision = ResearchDecision.INCONCLUSIVE

        self._transition(state, "Report", "synthesize honest research report")
        report = build_report(
            research_id=request.research_id,
            question=request.user_question,
            decision=state.decision,
            budget_snapshot=budget.snapshot(),
            plan=state.plan,
            data_section=state.data_section,
            candidates=state.candidates,
            reviews=state.reviews,
            portfolio=state.portfolio,
            risk=state.risk,
            reproducibility={
                "code_commit": code_commit(),
                "dataset_id": state.dataset_id,
                "transitions": state.transition_log,
            },
        )
        self.db.upsert_json(
            "reports",
            "research_id",
            request.research_id,
            report.model_dump(mode="json"),
            decision=report.decision.value,
            created_at=report.created_at.isoformat(),
        )
        self.db.set_memory(
            f"research:{request.research_id}",
            "episodic",
            {"decision": report.decision.value, "question": request.user_question, "candidates": len(state.candidates)},
        )
        request.status = ResearchStatus.COMPLETED
        self.db.upsert_json(
            "research_requests",
            "research_id",
            request.research_id,
            request.model_dump(mode="json"),
            status=request.status.value,
            created_at=request.created_at.isoformat(),
        )
        self._transition(state, "END", f"decision={state.decision.value}")
        state.report = report
        return report

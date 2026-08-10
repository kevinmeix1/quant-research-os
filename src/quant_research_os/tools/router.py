"""Allowlisted agent tools — typed, logged, no arbitrary shell/execution."""

from __future__ import annotations

from enum import Enum
from typing import Any, Callable

import pandas as pd
from pydantic import BaseModel, Field

from quant_research_os.alpha.registry import AlphaRegistry, analyze_diversification, seed_momentum_library
from quant_research_os.data.catalog import (
    inspect_dataset,
    list_datasets,
    load_dataset,
    query_market_data,
    validate_dataset,
)
from quant_research_os.domain.alpha import Alpha
from quant_research_os.domain.enums import AlphaStatus
from quant_research_os.domain.experiment import Experiment
from quant_research_os.domain.strategy import Strategy
from quant_research_os.engine.costs import CostAssumption, TransactionCostModel
from quant_research_os.engine.cross_sectional import CrossSectionalConfig, run_cross_sectional_backtest
from quant_research_os.engine.metrics import calculate_metrics
from quant_research_os.engine.portfolio import allocate_portfolio, run_stress_tests
from quant_research_os.engine.regime import analyze_regimes
from quant_research_os.engine.robustness import analyze_parameter_surface
from quant_research_os.engine.statistics import bootstrap_sharpe
from quant_research_os.engine.walk_forward import WalkForwardConfig, WindowMode, run_walk_forward
from quant_research_os.experiments.registry import ExperimentRegistry
from quant_research_os.storage.db import ResearchDB


class ToolKind(str, Enum):
    READ = "READ"
    WRITE = "WRITE"
    EXECUTION = "EXECUTION"


class ToolSpec(BaseModel):
    name: str
    kind: ToolKind
    description: str


class ToolResult(BaseModel):
    tool: str
    ok: bool
    data: dict[str, Any] = Field(default_factory=dict)
    error: str | None = None


class ToolContext:
    def __init__(self, db: ResearchDB | None = None, research_id: str | None = None) -> None:
        self.db = db or ResearchDB()
        self.research_id = research_id
        self.experiments = ExperimentRegistry(self.db)
        self.alphas = AlphaRegistry(self.db)
        self._return_cache: dict[str, pd.Series] = {}

    def log(self, tool: str, payload: dict[str, Any]) -> None:
        if self.research_id:
            self.db.add_trace(self.research_id, "tool", tool, payload)


def _ok(tool: str, data: dict[str, Any]) -> ToolResult:
    return ToolResult(tool=tool, ok=True, data=data)


def _err(tool: str, error: str) -> ToolResult:
    return ToolResult(tool=tool, ok=False, error=error)


class ToolRouter:
    """Allowlisted tools only. No shell. No live trading."""

    def __init__(self, ctx: ToolContext) -> None:
        self.ctx = ctx
        self._handlers: dict[str, Callable[..., ToolResult]] = {
            "list_datasets": self.list_datasets,
            "inspect_dataset": self.inspect_dataset,
            "validate_dataset": self.validate_dataset,
            "query_market_data": self.query_market_data,
            "list_strategies": self.list_strategies,
            "inspect_strategy": self.inspect_strategy,
            "list_alphas": self.list_alphas,
            "inspect_alpha": self.inspect_alpha,
            "analyze_existing_alpha_library": self.analyze_existing_alpha_library,
            "create_experiment": self.create_experiment,
            "run_backtest": self.run_backtest,
            "run_walk_forward": self.run_walk_forward,
            "run_bootstrap": self.run_bootstrap,
            "run_robustness_analysis": self.run_robustness_analysis,
            "analyze_regimes": self.analyze_regimes_tool,
            "analyze_diversification": self.analyze_diversification_tool,
            "optimize_portfolio": self.optimize_portfolio,
            "run_stress_test": self.run_stress_test,
            "save_alpha": self.save_alpha,
            "reject_alpha": self.reject_alpha,
            "calculate_metrics": self.calculate_metrics_tool,
            "calculate_correlations": self.calculate_correlations,
            "retrieve_research": self.retrieve_research,
            "retrieve_experiment": self.retrieve_experiment,
            "seed_momentum_baseline": self.seed_momentum_baseline,
        }

    def specs(self) -> list[ToolSpec]:
        return [
            ToolSpec(name=n, kind=ToolKind.READ if n.startswith(("list", "inspect", "retrieve", "validate", "query", "analyze", "calculate")) or n in {"run_bootstrap"} else (ToolKind.EXECUTION if n.startswith("run_") or n == "optimize_portfolio" else ToolKind.WRITE), description=n)
            for n in self._handlers
        ]

    def call(self, name: str, **kwargs: Any) -> ToolResult:
        if name not in self._handlers:
            return _err(name, f"tool not allowlisted: {name}")
        try:
            result = self._handlers[name](**kwargs)
            safe_kwargs = {
                k: (f"<{len(v)} floats>" if isinstance(v, list) and len(v) > 20 else v)
                for k, v in kwargs.items()
            }
            self.ctx.log(name, {"kwargs": safe_kwargs, "ok": result.ok, "error": result.error})
            return result
        except Exception as exc:
            err = _err(name, str(exc))
            self.ctx.log(name, {"kwargs": {k: type(v).__name__ for k, v in kwargs.items()}, "ok": False, "error": str(exc)})
            return err

    # --- handlers ---

    def list_datasets(self) -> ToolResult:
        return _ok("list_datasets", {"datasets": [d.model_dump() for d in list_datasets()]})

    def inspect_dataset(self, dataset_id: str) -> ToolResult:
        return _ok("inspect_dataset", inspect_dataset(dataset_id))

    def validate_dataset(self, dataset_id: str) -> ToolResult:
        report = validate_dataset(dataset_id)
        return _ok("validate_dataset", report.model_dump(mode="json"))

    def query_market_data(self, dataset_id: str, start: str | None = None, end: str | None = None) -> ToolResult:
        px = query_market_data(dataset_id, start, end)
        return _ok(
            "query_market_data",
            {
                "dataset_id": dataset_id,
                "n_rows": len(px),
                "n_instruments": px.shape[1],
                "start": str(px.index.min()),
                "end": str(px.index.max()),
            },
        )

    def list_strategies(self) -> ToolResult:
        return _ok("list_strategies", {"strategies": [s.model_dump(mode="json") for s in self.ctx.alphas.list_strategies()]})

    def inspect_strategy(self, strategy_id: str) -> ToolResult:
        s = self.ctx.alphas.get_strategy(strategy_id)
        if not s:
            return _err("inspect_strategy", "not found")
        return _ok("inspect_strategy", s.model_dump(mode="json"))

    def list_alphas(self) -> ToolResult:
        return _ok("list_alphas", {"alphas": [a.model_dump(mode="json") for a in self.ctx.alphas.list()]})

    def inspect_alpha(self, alpha_id: str) -> ToolResult:
        a = self.ctx.alphas.get(alpha_id)
        if not a:
            return _err("inspect_alpha", "not found")
        return _ok("inspect_alpha", a.model_dump(mode="json"))

    def analyze_existing_alpha_library(self) -> ToolResult:
        alphas = self.ctx.alphas.list()
        returns = {}
        for a in alphas:
            rets = a.robustness.get("returns")
            if rets:
                returns[a.alpha_id] = pd.Series(rets)
        corr = {}
        if len(returns) >= 2:
            df = pd.DataFrame(returns).corr()
            corr = df.round(4).to_dict()
        return _ok(
            "analyze_existing_alpha_library",
            {
                "n_alphas": len(alphas),
                "statuses": {a.alpha_id: a.status.value for a in alphas},
                "correlations": corr,
            },
        )

    def create_experiment(
        self,
        research_id: str,
        strategy_id: str | None = None,
        hypothesis_id: str | None = None,
        dataset_id: str = "fx_synthetic_momentum",
        parameters: dict | None = None,
        transaction_cost_model: str = "baseline",
        random_seed: int = 42,
    ) -> ToolResult:
        exp = Experiment(
            research_id=research_id,
            strategy_id=strategy_id,
            hypothesis_id=hypothesis_id,
            dataset_id=dataset_id,
            parameters=parameters or {},
            transaction_cost_model=transaction_cost_model,
            random_seed=random_seed,
        )
        exp = self.ctx.experiments.create(exp)
        return _ok("create_experiment", exp.model_dump(mode="json"))

    def run_backtest(
        self,
        dataset_id: str,
        signal_name: str = "momentum",
        lookback: int = 20,
        top_n: int = 3,
        bottom_n: int = 3,
        rebalance_every: int = 5,
        cost_assumption: str = "baseline",
        experiment_id: str | None = None,
        strategy_id: str | None = None,
    ) -> ToolResult:
        prices = load_dataset(dataset_id)
        cfg = CrossSectionalConfig(
            signal_name=signal_name,
            lookback=lookback,
            top_n=top_n,
            bottom_n=bottom_n,
            rebalance_every=rebalance_every,
            cost_assumption=CostAssumption(cost_assumption),
        )
        result = run_cross_sectional_backtest(
            prices,
            cfg,
            cost_model=TransactionCostModel.for_assumption(cost_assumption),
        )
        result.experiment_id = experiment_id
        result.strategy_id = strategy_id
        self.ctx.experiments.save_backtest(result)
        self.ctx._return_cache[result.backtest_id] = pd.Series(result.returns)
        if experiment_id:
            self.ctx.experiments.complete(experiment_id)
        return _ok(
            "run_backtest",
            {
                "backtest_id": result.backtest_id,
                "metrics": result.metrics.model_dump(),
                "provenance": result.provenance,
                "returns": result.returns,
            },
        )

    def run_walk_forward(
        self,
        dataset_id: str,
        signal_name: str = "momentum",
        lookback: int = 20,
        rebalance_every: int = 5,
        mode: str = "expanding_window",
        cost_assumption: str = "baseline",
    ) -> ToolResult:
        prices = load_dataset(dataset_id)
        cs = CrossSectionalConfig(
            signal_name=signal_name,
            lookback=lookback,
            rebalance_every=rebalance_every,
            cost_assumption=CostAssumption(cost_assumption),
        )
        wf = WalkForwardConfig(mode=WindowMode(mode), cost_assumption=CostAssumption(cost_assumption))
        result = run_walk_forward(prices, cs, wf)
        return _ok("run_walk_forward", result.model_dump(mode="json"))

    def run_bootstrap(self, returns: list[float], n_trials_tested: int = 1, seed: int = 42) -> ToolResult:
        result = bootstrap_sharpe(returns, n_trials_tested=n_trials_tested, seed=seed)
        return _ok("run_bootstrap", result.model_dump())

    def run_robustness_analysis(
        self,
        dataset_id: str,
        signal_name: str = "momentum",
        parameter_name: str = "lookback",
        values: list[int] | None = None,
        rebalance_every: int = 5,
    ) -> ToolResult:
        prices = load_dataset(dataset_id)
        cfg = CrossSectionalConfig(signal_name=signal_name, rebalance_every=rebalance_every)
        result = analyze_parameter_surface(prices, cfg, parameter_name=parameter_name, values=values)
        return _ok("run_robustness_analysis", result.model_dump())

    def analyze_regimes_tool(self, returns: list[float]) -> ToolResult:
        result = analyze_regimes(pd.Series(returns))
        # Don't dump huge label lists fully
        data = result.model_dump()
        data["regime_labels"] = data["regime_labels"][-20:]
        data["n_labels"] = len(result.regime_labels)
        return _ok("analyze_regimes", data)

    def analyze_diversification_tool(self, candidate_returns: list[float], against_alpha_ids: list[str] | None = None) -> ToolResult:
        existing = {}
        alphas = self.ctx.alphas.list()
        for a in alphas:
            if against_alpha_ids and a.alpha_id not in against_alpha_ids:
                continue
            if a.robustness.get("returns"):
                existing[a.alpha_id] = pd.Series(a.robustness["returns"])
        result = analyze_diversification(pd.Series(candidate_returns), existing)
        return _ok("analyze_diversification", result)

    def optimize_portfolio(self, returns_by_alpha: dict[str, list[float]], method: str = "volatility_scaling") -> ToolResult:
        series = {k: pd.Series(v) for k, v in returns_by_alpha.items()}
        alloc = allocate_portfolio(series, method=method)
        return _ok("optimize_portfolio", alloc.model_dump())

    def run_stress_test(self, returns: list[float]) -> ToolResult:
        results = run_stress_tests(pd.Series(returns))
        return _ok("run_stress_test", {"scenarios": [r.model_dump() for r in results]})

    def save_alpha(
        self,
        strategy_id: str,
        hypothesis: str,
        mechanism: str,
        universe: str,
        features: list[str],
        metrics: dict[str, float],
        metrics_source_ids: list[str],
        returns: list[float] | None = None,
        status: str = "PROMISING",
        extras: dict | None = None,
    ) -> ToolResult:
        alpha = Alpha(
            strategy_id=strategy_id,
            hypothesis=hypothesis,
            expected_economic_mechanism=mechanism,
            universe=universe,
            features=features,
            metrics=metrics,
            metrics_source_ids=metrics_source_ids,
            status=AlphaStatus(status),
            robustness={**(extras or {}), **({"returns": returns} if returns is not None else {})},
        )
        alpha = self.ctx.alphas.save(alpha)
        return _ok("save_alpha", alpha.model_dump(mode="json"))

    def reject_alpha(self, alpha_id: str, reason: str) -> ToolResult:
        alpha = self.ctx.alphas.reject(alpha_id, reason)
        return _ok("reject_alpha", alpha.model_dump(mode="json"))

    def calculate_metrics_tool(self, returns: list[float]) -> ToolResult:
        m = calculate_metrics(pd.Series(returns))
        return _ok("calculate_metrics", m.model_dump())

    def calculate_correlations(self, returns_by_id: dict[str, list[float]]) -> ToolResult:
        df = pd.DataFrame({k: pd.Series(v) for k, v in returns_by_id.items()}).corr()
        return _ok("calculate_correlations", {"matrix": df.round(4).to_dict()})

    def retrieve_research(self, research_id: str) -> ToolResult:
        raw = self.ctx.db.get_json("research_requests", "research_id", research_id)
        if not raw:
            return _err("retrieve_research", "not found")
        return _ok("retrieve_research", raw)

    def retrieve_experiment(self, experiment_id: str) -> ToolResult:
        exp = self.ctx.experiments.get(experiment_id)
        if not exp:
            return _err("retrieve_experiment", "not found")
        return _ok("retrieve_experiment", exp.model_dump(mode="json"))

    def seed_momentum_baseline(self, dataset_id: str = "fx_synthetic_momentum") -> ToolResult:
        prices = load_dataset(dataset_id)
        cfg = CrossSectionalConfig(signal_name="momentum", lookback=20)
        bt = run_cross_sectional_backtest(prices, cfg, cost_model=TransactionCostModel.for_assumption("baseline"))
        alpha = seed_momentum_library(self.ctx.alphas, pd.Series(bt.returns))
        return _ok("seed_momentum_baseline", {"alpha": alpha.model_dump(mode="json"), "backtest_id": bt.backtest_id})

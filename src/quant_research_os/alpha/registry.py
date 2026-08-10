"""Alpha library: lifecycle, metrics provenance, correlation analysis."""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd

from quant_research_os.domain.alpha import Alpha
from quant_research_os.domain.enums import AlphaStatus
from quant_research_os.domain.strategy import Strategy
from quant_research_os.storage.db import ResearchDB


class AlphaRegistry:
    def __init__(self, db: ResearchDB | None = None) -> None:
        self.db = db or ResearchDB()

    def save_strategy(self, strategy: Strategy) -> Strategy:
        self.db.upsert_json(
            "strategies",
            "strategy_id",
            strategy.strategy_id,
            strategy.model_dump(mode="json"),
            version=strategy.version,
        )
        if strategy.parent_strategy_id:
            self.db.add_edge(
                "strategy",
                strategy.parent_strategy_id,
                "versioned_to",
                "strategy",
                strategy.strategy_id,
            )
        return strategy

    def get_strategy(self, strategy_id: str) -> Strategy | None:
        raw = self.db.get_json("strategies", "strategy_id", strategy_id)
        return Strategy.model_validate(raw) if raw else None

    def list_strategies(self) -> list[Strategy]:
        return [Strategy.model_validate(r) for r in self.db.list_json("strategies")]

    def save(self, alpha: Alpha) -> Alpha:
        # Refuse metrics without provenance
        if alpha.metrics and not alpha.metrics_source_ids:
            raise ValueError("Alpha metrics require metrics_source_ids from deterministic tools")
        self.db.upsert_json(
            "alphas",
            "alpha_id",
            alpha.alpha_id,
            alpha.model_dump(mode="json"),
            strategy_id=alpha.strategy_id,
            status=alpha.status.value,
        )
        self.db.add_edge("strategy", alpha.strategy_id, "instantiates", "alpha", alpha.alpha_id)
        return alpha

    def get(self, alpha_id: str) -> Alpha | None:
        raw = self.db.get_json("alphas", "alpha_id", alpha_id)
        return Alpha.model_validate(raw) if raw else None

    def list(self, status: AlphaStatus | None = None) -> list[Alpha]:
        rows = self.db.list_json("alphas")
        alphas = [Alpha.model_validate(r) for r in rows]
        if status:
            alphas = [a for a in alphas if a.status == status]
        return alphas

    def set_status(self, alpha_id: str, status: AlphaStatus) -> Alpha:
        alpha = self.get(alpha_id)
        if not alpha:
            raise KeyError(alpha_id)
        alpha.status = status
        return self.save(alpha)

    def reject(self, alpha_id: str, reason: str) -> Alpha:
        alpha = self.get(alpha_id)
        if not alpha:
            raise KeyError(alpha_id)
        alpha.status = AlphaStatus.REJECTED
        alpha.robustness = {**alpha.robustness, "reject_reason": reason}
        return self.save(alpha)


def correlation_matrix(returns: dict[str, pd.Series]) -> pd.DataFrame:
    df = pd.DataFrame(returns).dropna(how="any")
    if df.empty:
        return pd.DataFrame()
    return df.corr()


def analyze_diversification(
    candidate_returns: pd.Series,
    existing_returns: dict[str, pd.Series],
) -> dict[str, Any]:
    """Deterministic diversification diagnostics vs existing alpha library."""
    out: dict[str, Any] = {
        "return_correlations": {},
        "downside_correlations": {},
        "avg_correlation": None,
        "max_correlation": None,
        "incremental_sharpe_hint": None,
        "genuine_diversification": None,
    }
    if candidate_returns.empty or not existing_returns:
        out["genuine_diversification"] = True
        out["avg_correlation"] = 0.0
        out["max_correlation"] = 0.0
        return out

    corrs = []
    down_corrs = []
    for name, series in existing_returns.items():
        aligned = pd.concat(
            [candidate_returns.rename("c"), series.rename("e")],
            axis=1,
        ).dropna()
        if len(aligned) < 10:
            continue
        corr = float(aligned["c"].corr(aligned["e"]))
        out["return_correlations"][name] = corr
        corrs.append(corr)
        mask = (aligned["c"] < 0) | (aligned["e"] < 0)
        if mask.sum() >= 10:
            dc = float(aligned.loc[mask, "c"].corr(aligned.loc[mask, "e"]))
            out["downside_correlations"][name] = dc
            down_corrs.append(dc)

    if corrs:
        out["avg_correlation"] = float(np.mean(corrs))
        out["max_correlation"] = float(np.max(np.abs(corrs)))
        # Heuristic: low return corr AND low downside corr → more genuine diversification
        avg_down = float(np.mean(down_corrs)) if down_corrs else out["avg_correlation"]
        out["genuine_diversification"] = abs(out["avg_correlation"]) < 0.35 and abs(avg_down) < 0.45

        # Equal-weight portfolio vs existing-only Sharpe hint
        exist_df = pd.DataFrame(existing_returns).dropna(how="all")
        if not exist_df.empty:
            port_old = exist_df.mean(axis=1)
            port_new = pd.concat([port_old, candidate_returns], axis=1).dropna().mean(axis=1)
            def _sharpe(r: pd.Series) -> float:
                if r.std(ddof=0) == 0:
                    return 0.0
                return float(r.mean() / r.std(ddof=0) * np.sqrt(252))
            out["incremental_sharpe_hint"] = {
                "existing_sharpe": _sharpe(port_old),
                "with_candidate_sharpe": _sharpe(port_new),
                "delta": _sharpe(port_new) - _sharpe(port_old),
            }
    else:
        out["genuine_diversification"] = True
        out["avg_correlation"] = 0.0
        out["max_correlation"] = 0.0
    return out


def seed_momentum_library(
    registry: AlphaRegistry,
    momentum_returns: pd.Series,
    *,
    universe: str = "FX_G10",
) -> Alpha:
    """Seed a singleton 'existing momentum' alpha (idempotent)."""
    fixed_strategy_id = "STR-existing-momentum"
    fixed_alpha_id = "ALP-existing-momentum"
    existing = registry.get(fixed_alpha_id)
    if existing is not None:
        return existing

    strategy = Strategy(
        strategy_id=fixed_strategy_id,
        name="existing_cross_sectional_momentum",
        description="Baseline momentum book already in the library",
        economic_rationale="Trend continuation in FX cross-section",
        universe=universe,
        features=["momentum_20d"],
        signal_definition="rank(momentum)",
        version="1",
    )
    registry.save_strategy(strategy)
    from quant_research_os.engine.metrics import calculate_metrics

    metrics = calculate_metrics(momentum_returns)
    alpha = Alpha(
        alpha_id=fixed_alpha_id,
        strategy_id=strategy.strategy_id,
        hypothesis="Existing momentum exposure",
        expected_economic_mechanism="cross-sectional trend following",
        features=["momentum_20d"],
        universe=universe,
        metrics=metrics.model_dump(exclude_none=True),
        metrics_source_ids=["seed:momentum"],
        status=AlphaStatus.ROBUST,
    )
    alpha.robustness = {
        "returns": momentum_returns.tolist(),
        "seed": True,
    }
    return registry.save(alpha)

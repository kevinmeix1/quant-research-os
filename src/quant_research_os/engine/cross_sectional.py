"""Cross-sectional long/short backtest engine (Phase 1 v0).

Timing contract (anti look-ahead):
  1. At bar t close, compute signal from prices available at t.
  2. Target weights are scheduled for execution at bar t + execution_lag.
  3. Default execution_lag=1 → no same-bar return on new weights.
  4. Between rebalances, share holdings are held fixed (weights drift).
"""

from __future__ import annotations

from enum import Enum

import numpy as np
import pandas as pd
from pydantic import BaseModel, Field

from quant_research_os.domain.backtest import BacktestResult
from quant_research_os.engine.costs import CostAssumption, TransactionCostModel, apply_cost_series
from quant_research_os.engine.metrics import calculate_metrics


class SelectionMethod(str, Enum):
    TOP_BOTTOM_N = "top_bottom_n"
    PERCENTILE = "percentile"
    ZSCORE_WEIGHT = "zscore_weight"
    RANK_WEIGHT = "rank_weight"


class CrossSectionalConfig(BaseModel):
    lookback: int = 20
    top_n: int = 3
    bottom_n: int = 3
    selection: SelectionMethod = SelectionMethod.TOP_BOTTOM_N
    percentile_long: float = 0.8
    percentile_short: float = 0.2
    rebalance_every: int = 5
    execution_lag: int = Field(default=1, ge=1, description="Bars between signal and execution.")
    gross_exposure: float = 1.0
    cost_assumption: CostAssumption = CostAssumption.BASELINE
    risk_free_rate: float = 0.0
    signal_name: str = "momentum"


def momentum_signal(prices: pd.DataFrame, lookback: int) -> pd.DataFrame:
    return prices / prices.shift(lookback) - 1.0


def reversal_signal(prices: pd.DataFrame, lookback: int) -> pd.DataFrame:
    return -momentum_signal(prices, lookback)


def _signal_matrix(prices: pd.DataFrame, cfg: CrossSectionalConfig) -> pd.DataFrame:
    """Build CS scores without future information (features use only past prices)."""
    from quant_research_os.features.library import FEATURE_GENERATORS

    name = cfg.signal_name
    if name in FEATURE_GENERATORS:
        return FEATURE_GENERATORS[name](prices, cfg.lookback)
    if name == "momentum":
        return momentum_signal(prices, cfg.lookback)
    if name == "reversal":
        return reversal_signal(prices, cfg.lookback)
    raise ValueError(f"unknown signal_name: {name}")


def scores_to_weights(scores: pd.Series, cfg: CrossSectionalConfig) -> pd.Series:
    s = scores.dropna()
    w = pd.Series(0.0, index=scores.index)
    if s.empty:
        return w

    method = cfg.selection
    if method == SelectionMethod.TOP_BOTTOM_N:
        long = s.nlargest(min(cfg.top_n, len(s))).index
        short = s.nsmallest(min(cfg.bottom_n, len(s))).index
    elif method == SelectionMethod.PERCENTILE:
        long = s[s >= s.quantile(cfg.percentile_long)].index
        short = s[s <= s.quantile(cfg.percentile_short)].index
    elif method == SelectionMethod.ZSCORE_WEIGHT:
        z = (s - s.mean()) / (s.std(ddof=0) + 1e-12)
        w = z.reindex(scores.index).fillna(0.0)
        gross = float(w.abs().sum())
        if gross > 0:
            w = w * (cfg.gross_exposure / gross)
        return w
    else:  # RANK_WEIGHT
        ranks = s.rank(method="average")
        centered = ranks - ranks.mean()
        w = centered.reindex(scores.index).fillna(0.0)
        gross = float(w.abs().sum())
        if gross > 0:
            w = w * (cfg.gross_exposure / gross)
        return w

    if len(long):
        w.loc[long] = cfg.gross_exposure / (2 * len(long))
    if len(short):
        w.loc[short] = -cfg.gross_exposure / (2 * len(short))
    return w


def run_cross_sectional_backtest(
    prices: pd.DataFrame,
    cfg: CrossSectionalConfig | None = None,
    *,
    cost_model: TransactionCostModel | None = None,
) -> BacktestResult:
    cfg = cfg or CrossSectionalConfig()
    if cfg.execution_lag < 1:
        raise ValueError("execution_lag must be >= 1 to prevent same-bar look-ahead")

    prices = prices.sort_index().astype(float)
    if prices.shape[1] < 2:
        raise ValueError("need >= 2 instruments for cross-sectional backtest")

    cost_model = cost_model or TransactionCostModel.for_assumption(cfg.cost_assumption)
    signals = _signal_matrix(prices, cfg)
    asset_rets = prices.pct_change().fillna(0.0)

    n = len(prices)
    cols = prices.columns
    target = pd.DataFrame(np.nan, index=prices.index, columns=cols)

    for i in range(cfg.lookback, n, cfg.rebalance_every):
        dt = prices.index[i]
        target.loc[dt] = scores_to_weights(signals.loc[dt], cfg)

    # Schedule execution lag bars later.
    scheduled = target.shift(cfg.execution_lag)

    # Holdings = portfolio weights at start-of-bar (sum of abs ≈ gross_exposure at last rebalance).
    holdings = pd.Series(0.0, index=cols)
    port_rets = np.zeros(n)
    turnovers = np.zeros(n)
    trade_count = 0

    for i in range(1, n):
        dt = prices.index[i]
        r_i = asset_rets.loc[dt].fillna(0.0)

        # Rebalance using current *weights* (not drifted notionals) so turnover is in weight space.
        sched = scheduled.loc[dt]
        if sched.notna().any():
            new_w = sched.fillna(0.0)
            cur_w = holdings.copy()
            turnover = float((new_w - cur_w).abs().sum() / 2.0)
            turnovers[i] = turnover
            if turnover > 1e-12:
                trade_count += int((new_w - cur_w).abs().gt(1e-12).sum())
            holdings = new_w.copy()

        # Simple return on beginning-of-bar weights.
        port_ret = float((holdings * r_i).sum())
        port_rets[i] = port_ret

        # Fixed-share drift, then renormalize to weights so next day's return is PnL/NAV.
        drifted = holdings * (1.0 + r_i)
        denom = 1.0 + port_ret
        if abs(denom) > 1e-12:
            holdings = drifted / denom
        else:
            holdings = drifted * 0.0

    ret_series = pd.Series(port_rets, index=prices.index).iloc[1:]
    turn_series = pd.Series(turnovers, index=prices.index).iloc[1:]
    cost_series, cost_summary = apply_cost_series(turn_series, cost_model)
    net = ret_series - cost_series.reindex(ret_series.index).fillna(0.0)

    metrics = calculate_metrics(
        net,
        risk_free_rate=cfg.risk_free_rate,
        turnover_series=turn_series.reindex(net.index),
        total_transaction_costs=cost_summary.proportional
        + cost_summary.spread
        + cost_summary.fixed,
        total_slippage=cost_summary.slippage,
        trade_count=trade_count,
    )
    equity = (1 + net).cumprod()

    return BacktestResult(
        metrics=metrics,
        returns=net.tolist(),
        cumulative_returns=equity.tolist(),
        metadata={
            "config": cfg.model_dump(mode="json"),
            "cost_model": cost_model.model_dump(mode="json"),
            "execution_lag": cfg.execution_lag,
            "cost_summary": cost_summary.model_dump(),
        },
        provenance={
            "engine": "quant_research_os.engine.cross_sectional",
            "engine_version": "0.1.0",
        },
    )

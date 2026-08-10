"""Performance metrics — pinned local deterministic implementation.

Financial metrics must never be invented by LLMs. This module is the
sole calculation surface for agents/tools (sibling import disabled to
avoid environment-dependent Sharpe from ddof mismatches).
"""

from __future__ import annotations

import math

import numpy as np
import pandas as pd

from quant_research_os.domain.backtest import PerformanceMetrics


def sibling_metrics_available() -> bool:
    """Always False — QROS pins its own metrics for reproducibility."""
    return False


def calculate_metrics(
    daily_returns: pd.Series | list[float] | np.ndarray,
    *,
    risk_free_rate: float = 0.0,
    turnover_series: pd.Series | list[float] | np.ndarray | None = None,
    total_transaction_costs: float = 0.0,
    total_slippage: float = 0.0,
    trade_count: int = 0,
    periods_per_year: int = 252,
) -> PerformanceMetrics:
    """Compute performance metrics from a return series (deterministic, local)."""
    r = pd.Series(daily_returns, dtype=float).dropna()
    turn = None
    if turnover_series is not None:
        turn = pd.Series(turnover_series, dtype=float)
        if len(turn) != len(pd.Series(daily_returns)):
            turn = turn.reindex(r.index) if hasattr(turn, "index") else turn

    return _local_metrics(
        r,
        risk_free_rate=risk_free_rate,
        turnover_series=turn,
        total_transaction_costs=total_transaction_costs,
        total_slippage=total_slippage,
        trade_count=trade_count,
        periods_per_year=periods_per_year,
    )


def _local_metrics(
    r: pd.Series,
    *,
    risk_free_rate: float,
    turnover_series: pd.Series | None,
    total_transaction_costs: float,
    total_slippage: float,
    trade_count: int,
    periods_per_year: int = 252,
) -> PerformanceMetrics:
    if r.empty:
        return PerformanceMetrics()

    equity = (1 + r).cumprod()
    cum = float(equity.iloc[-1] - 1)
    ann_factor = periods_per_year
    ann_ret = float((1 + cum) ** (ann_factor / len(r)) - 1) if len(r) > 0 else 0.0
    vol = float(r.std(ddof=0) * math.sqrt(ann_factor)) if len(r) else 0.0
    excess = r - risk_free_rate / ann_factor
    sharpe = float(excess.mean() / r.std(ddof=0) * math.sqrt(ann_factor)) if r.std(ddof=0) > 0 else 0.0
    # Full-sample downside deviation vs 0 (not std of negative subset only).
    downside = np.minimum(r.to_numpy(dtype=float), 0.0)
    down_dev = float(np.sqrt(np.mean(downside**2))) if len(downside) else 0.0
    sortino = (
        float(excess.mean() / down_dev * math.sqrt(ann_factor)) if down_dev > 0 else 0.0
    )
    roll_max = equity.cummax()
    mdd = float((equity / roll_max - 1.0).min())
    calmar = float(ann_ret / abs(mdd)) if mdd < 0 else 0.0
    avg_turn = float(turnover_series.mean()) if turnover_series is not None and len(turnover_series) else 0.0

    return PerformanceMetrics(
        annual_return=ann_ret,
        volatility=vol,
        sharpe=sharpe,
        sortino=sortino,
        max_drawdown=mdd,
        calmar=calmar,
        turnover=avg_turn,
        transaction_costs=float(total_transaction_costs),
        slippage=float(total_slippage),
        cumulative_return=cum,
        trade_count=int(trade_count),
    )

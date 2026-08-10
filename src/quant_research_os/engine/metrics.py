"""Performance metrics — prefer sibling portfolio-agent implementation.

Financial metrics must never be invented by LLMs. This module is the
deterministic calculation surface for agents/tools.
"""

from __future__ import annotations

import math

import numpy as np
import pandas as pd

from quant_research_os.domain.backtest import PerformanceMetrics

_SIBLING_AVAILABLE: bool | None = None
_SIBLING_FN = None


def _load_sibling_compute():
    """Load sibling metrics without importing portfolio.eval package __init__.

    Sibling `eval/__init__.py` eagerly imports backtest → optimizer → pypfopt.
    We only need the pure metrics module.
    """
    import importlib.util
    from pathlib import Path

    # trading operating system/ → sibling x11/src/portfolio/eval/metrics.py
    here = Path(__file__).resolve()
    candidate = here.parents[4] / "src" / "portfolio" / "eval" / "metrics.py"
    if not candidate.exists():
        # Fallback: installed package path if layout differs
        try:
            import portfolio

            candidate = Path(portfolio.__file__).resolve().parent / "eval" / "metrics.py"
        except ImportError:
            return None
    if not candidate.exists():
        return None

    import sys

    spec = importlib.util.spec_from_file_location(
        "qros_sibling_portfolio_metrics",
        candidate,
    )
    if spec is None or spec.loader is None:
        return None
    mod = importlib.util.module_from_spec(spec)
    # Required before exec_module so @dataclass can resolve cls.__module__.
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return getattr(mod, "compute_performance_metrics", None)


def _try_sibling_metrics():
    global _SIBLING_AVAILABLE, _SIBLING_FN
    if _SIBLING_AVAILABLE is not None:
        return _SIBLING_FN
    try:
        fn = _load_sibling_compute()
        _SIBLING_FN = fn
        _SIBLING_AVAILABLE = fn is not None
        return fn
    except Exception:
        _SIBLING_AVAILABLE = False
        _SIBLING_FN = None
        return None


def sibling_metrics_available() -> bool:
    if _SIBLING_AVAILABLE is None:
        _try_sibling_metrics()
    return bool(_SIBLING_AVAILABLE)


def calculate_metrics(
    daily_returns: pd.Series | list[float] | np.ndarray,
    *,
    risk_free_rate: float = 0.0,
    turnover_series: pd.Series | list[float] | np.ndarray | None = None,
    total_transaction_costs: float = 0.0,
    total_slippage: float = 0.0,
    trade_count: int = 0,
) -> PerformanceMetrics:
    """Compute performance metrics from a return series.

    Uses sibling `portfolio.eval.metrics.compute_performance_metrics` when
    available; otherwise a local equivalent. Both are deterministic.
    """
    r = pd.Series(daily_returns, dtype=float).dropna()
    turn = None
    if turnover_series is not None:
        turn = pd.Series(turnover_series, dtype=float)
        if len(turn) != len(pd.Series(daily_returns)):
            # align to returns length if caller passed full history
            turn = turn.reindex(r.index) if hasattr(turn, "index") else turn

    sibling = _try_sibling_metrics()
    if sibling is not None:
        raw = sibling(r, risk_free_rate=risk_free_rate, turnover_series=turn)
        return PerformanceMetrics(
            annual_return=float(raw.annualized_return),
            volatility=float(raw.annualized_volatility),
            sharpe=float(raw.sharpe_ratio),
            sortino=float(raw.sortino_ratio),
            max_drawdown=float(raw.max_drawdown),
            calmar=float(raw.calmar_ratio),
            turnover=float(raw.avg_turnover),
            transaction_costs=float(total_transaction_costs),
            slippage=float(total_slippage),
            cumulative_return=float(raw.cumulative_return),
            trade_count=int(trade_count),
        )

    return _local_metrics(
        r,
        risk_free_rate=risk_free_rate,
        turnover_series=turn,
        total_transaction_costs=total_transaction_costs,
        total_slippage=total_slippage,
        trade_count=trade_count,
    )


def _local_metrics(
    r: pd.Series,
    *,
    risk_free_rate: float,
    turnover_series: pd.Series | None,
    total_transaction_costs: float,
    total_slippage: float,
    trade_count: int,
) -> PerformanceMetrics:
    if r.empty:
        return PerformanceMetrics()

    equity = (1 + r).cumprod()
    cum = float(equity.iloc[-1] - 1)
    ann_factor = 252
    ann_ret = float((1 + cum) ** (ann_factor / len(r)) - 1) if len(r) > 0 else 0.0
    vol = float(r.std(ddof=0) * math.sqrt(ann_factor)) if len(r) else 0.0
    excess = r - risk_free_rate / ann_factor
    sharpe = float(excess.mean() / r.std(ddof=0) * math.sqrt(ann_factor)) if r.std(ddof=0) > 0 else 0.0
    downside = r[r < 0]
    sortino = (
        float(excess.mean() / downside.std(ddof=0) * math.sqrt(ann_factor))
        if len(downside) and downside.std(ddof=0) > 0
        else 0.0
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

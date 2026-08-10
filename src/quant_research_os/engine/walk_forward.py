"""Walk-forward validation with per-window metrics preserved."""

from __future__ import annotations

from enum import Enum
from typing import Any, Callable

import pandas as pd
from pydantic import BaseModel, Field

from quant_research_os.domain.backtest import PerformanceMetrics
from quant_research_os.engine.costs import CostAssumption, TransactionCostModel
from quant_research_os.engine.cross_sectional import CrossSectionalConfig, run_cross_sectional_backtest
from quant_research_os.engine.metrics import calculate_metrics


class WindowMode(str, Enum):
    EXPANDING = "expanding_window"
    ROLLING = "rolling_window"


class WalkForwardConfig(BaseModel):
    mode: WindowMode = WindowMode.EXPANDING
    train_bars: int = 126
    test_bars: int = 63
    step_bars: int = 63
    rolling_train_bars: int = 252
    cost_assumption: CostAssumption = CostAssumption.BASELINE


class WalkForwardWindow(BaseModel):
    window_id: int
    train_start: str
    train_end: str
    test_start: str
    test_end: str
    metrics: PerformanceMetrics
    n_test_bars: int


class WalkForwardResult(BaseModel):
    mode: WindowMode
    windows: list[WalkForwardWindow] = Field(default_factory=list)
    aggregate: dict[str, Any] = Field(default_factory=dict)
    oos_returns: list[float] = Field(default_factory=list)


def _window_bounds(n: int, cfg: WalkForwardConfig) -> list[tuple[int, int, int, int]]:
    """Return list of (train_start, train_end, test_start, test_end) exclusive end indices."""
    bounds = []
    if cfg.mode == WindowMode.EXPANDING:
        train_end = cfg.train_bars
        while train_end + cfg.test_bars <= n:
            test_start = train_end
            test_end = train_end + cfg.test_bars
            bounds.append((0, train_end, test_start, test_end))
            train_end += cfg.step_bars
    else:
        start = 0
        while start + cfg.rolling_train_bars + cfg.test_bars <= n:
            train_start = start
            train_end = start + cfg.rolling_train_bars
            test_start = train_end
            test_end = train_end + cfg.test_bars
            bounds.append((train_start, train_end, test_start, test_end))
            start += cfg.step_bars
    return bounds


def run_walk_forward(
    prices: pd.DataFrame,
    cs_cfg: CrossSectionalConfig,
    wf_cfg: WalkForwardConfig | None = None,
) -> WalkForwardResult:
    wf_cfg = wf_cfg or WalkForwardConfig()
    n = len(prices)
    bounds = _window_bounds(n, wf_cfg)
    windows: list[WalkForwardWindow] = []
    oos_parts: list[pd.Series] = []
    cost_model = TransactionCostModel.for_assumption(wf_cfg.cost_assumption)

    for i, (ts, te, vs, ve) in enumerate(bounds):
        # Fit is implicit in lookback signal; evaluate OOS segment with full history up to ve
        # but only keep OOS returns in [vs, ve).
        slice_prices = prices.iloc[:ve]
        result = run_cross_sectional_backtest(slice_prices, cs_cfg, cost_model=cost_model)
        rets = pd.Series(result.returns, index=slice_prices.index[1:])
        oos = rets.iloc[max(vs - 1, 0) : ve - 1]
        if oos.empty:
            continue
        metrics = calculate_metrics(oos, risk_free_rate=cs_cfg.risk_free_rate)
        windows.append(
            WalkForwardWindow(
                window_id=i,
                train_start=str(prices.index[ts].date()),
                train_end=str(prices.index[te - 1].date()),
                test_start=str(prices.index[vs].date()),
                test_end=str(prices.index[ve - 1].date()),
                metrics=metrics,
                n_test_bars=len(oos),
            )
        )
        oos_parts.append(oos)

    oos_all = pd.concat(oos_parts) if oos_parts else pd.Series(dtype=float)
    sharpes = [w.metrics.sharpe for w in windows]
    profitable = sum(1 for w in windows if w.metrics.cumulative_return > 0)
    aggregate = {
        "n_windows": len(windows),
        "pct_profitable_windows": (profitable / len(windows)) if windows else 0.0,
        "sharpe_mean": float(sum(sharpes) / len(sharpes)) if sharpes else 0.0,
        "sharpe_std": float(pd.Series(sharpes).std(ddof=0)) if len(sharpes) > 1 else 0.0,
        "sharpe_min": float(min(sharpes)) if sharpes else 0.0,
        "sharpe_max": float(max(sharpes)) if sharpes else 0.0,
        "worst_window_drawdown": float(min((w.metrics.max_drawdown for w in windows), default=0.0)),
        "oos_metrics": calculate_metrics(oos_all).model_dump() if len(oos_all) else {},
    }
    return WalkForwardResult(
        mode=wf_cfg.mode,
        windows=windows,
        aggregate=aggregate,
        oos_returns=oos_all.tolist(),
    )

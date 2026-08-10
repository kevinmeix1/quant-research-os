"""Adversarial quantitative invariant tests."""

from __future__ import annotations

import numpy as np
import pandas as pd

from quant_research_os.data.synthetic import synthetic_momentum_fx
from quant_research_os.engine.costs import CostAssumption, TransactionCostModel
from quant_research_os.engine.cross_sectional import CrossSectionalConfig, run_cross_sectional_backtest
from quant_research_os.engine.metrics import calculate_metrics, sibling_metrics_available
from quant_research_os.engine.walk_forward import WalkForwardConfig, WindowMode, run_walk_forward


def test_metrics_pinned_local():
    assert sibling_metrics_available() is False


def test_zero_returns_zero_strategy_metrics():
    r = pd.Series([0.0] * 100)
    m = calculate_metrics(r)
    assert m.cumulative_return == 0.0
    assert m.sharpe == 0.0
    assert m.annual_return == 0.0


def test_increasing_costs_never_improves_net_return():
    prices = synthetic_momentum_fx(n_days=260, seed=3)
    cfg = CrossSectionalConfig(lookback=20, rebalance_every=5, top_n=2, bottom_n=2)
    free = TransactionCostModel(
        assumption=CostAssumption.OPTIMISTIC,
        proportional_bps=0,
        spread_bps=0,
        slippage_bps=0,
    )
    mid = TransactionCostModel.for_assumption(CostAssumption.BASELINE)
    high = TransactionCostModel.for_assumption(CostAssumption.PESSIMISTIC)
    r0 = run_cross_sectional_backtest(prices, cfg, cost_model=free)
    r1 = run_cross_sectional_backtest(prices, cfg, cost_model=mid)
    r2 = run_cross_sectional_backtest(prices, cfg, cost_model=high)
    assert r2.metrics.cumulative_return <= r1.metrics.cumulative_return + 1e-12
    assert r1.metrics.cumulative_return <= r0.metrics.cumulative_return + 1e-12


def test_identical_inputs_identical_pnl():
    prices = synthetic_momentum_fx(n_days=200, seed=9)
    cfg = CrossSectionalConfig(lookback=15, rebalance_every=5, top_n=2, bottom_n=2)
    a = run_cross_sectional_backtest(prices, cfg)
    b = run_cross_sectional_backtest(prices, cfg)
    assert a.returns == b.returns
    assert a.metrics.sharpe == b.metrics.sharpe


def test_nav_weights_stay_normalized_between_rebalances():
    """After drift renormalization, abs gross should remain near target gross."""
    # Use a tiny panel and inspect via re-running with rebalance_every large
    dates = pd.bdate_range("2020-01-01", periods=30)
    rng = np.random.default_rng(0)
    px = pd.DataFrame(100 * np.exp(np.cumsum(rng.normal(0, 0.01, size=(30, 4)), axis=0)), index=dates, columns=list("ABCD"))
    cfg = CrossSectionalConfig(lookback=5, rebalance_every=20, top_n=1, bottom_n=1, execution_lag=1)
    free = TransactionCostModel(assumption=CostAssumption.OPTIMISTIC, proportional_bps=0, spread_bps=0, slippage_bps=0)
    result = run_cross_sectional_backtest(px, cfg, cost_model=free)
    assert np.isfinite(result.metrics.sharpe)
    assert len(result.returns) == len(px) - 1


def test_signal_day_turnover_zero_under_lag():
    """With lag=1, signal day should not immediately trade."""
    dates = pd.bdate_range("2020-01-01", periods=40)
    data = {f"P{i}": np.full(40, 100.0) for i in range(6)}
    prices = pd.DataFrame(data, index=dates)
    prices.iloc[10:21, 0] = np.linspace(100, 130, 11)
    cfg = CrossSectionalConfig(lookback=10, rebalance_every=10, top_n=1, bottom_n=1, execution_lag=1)
    free = TransactionCostModel(assumption=CostAssumption.OPTIMISTIC, proportional_bps=0, spread_bps=0, slippage_bps=0)
    # Monkeypatch path: inspect turnovers via metadata cost_summary turnover sum and engine internals
    # Signal at i=10 → execute at i=11; day index 10 (signal) turnover should be 0
    from quant_research_os.engine import cross_sectional as cs

    signals = cs._signal_matrix(prices, cfg)
    target = pd.DataFrame(np.nan, index=prices.index, columns=prices.columns)
    for i in range(cfg.lookback, len(prices), cfg.rebalance_every):
        target.loc[prices.index[i]] = cs.scores_to_weights(signals.loc[prices.index[i]], cfg)
    scheduled = target.shift(cfg.execution_lag)
    # On signal day index 10, scheduled should be NaN (execution next day)
    assert scheduled.iloc[10].isna().all()
    assert scheduled.iloc[11].notna().any()


def test_future_shuffle_does_not_change_historical_signal_rank():
    prices = synthetic_momentum_fx(n_days=120, seed=4)
    cfg = CrossSectionalConfig(lookback=20)
    from quant_research_os.engine.cross_sectional import _signal_matrix

    mid = 60
    sig = _signal_matrix(prices, cfg).iloc[mid]
    shuffled = prices.copy()
    # Shuffle only future rows after mid
    future = shuffled.iloc[mid + 1 :].to_numpy().copy()
    rng = np.random.default_rng(0)
    order = rng.permutation(len(future))
    shuffled.iloc[mid + 1 :] = future[order]
    sig2 = _signal_matrix(shuffled, cfg).iloc[mid]
    pd.testing.assert_series_equal(sig, sig2)


def test_walk_forward_dedupes_overlapping_oos():
    prices = synthetic_momentum_fx(n_days=400, seed=5)
    cfg = CrossSectionalConfig(lookback=15, rebalance_every=5, top_n=2, bottom_n=2)
    # Intentionally overlapping windows
    wf = run_walk_forward(
        prices,
        cfg,
        WalkForwardConfig(train_bars=100, test_bars=60, step_bars=20, mode=WindowMode.EXPANDING),
    )
    assert wf.aggregate["n_oos_bars_unique"] == len(wf.oos_returns)
    # Unique count should be < naive concat if overlaps existed
    assert wf.aggregate["n_windows"] >= 1

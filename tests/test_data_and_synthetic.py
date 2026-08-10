from __future__ import annotations

from quant_research_os.data.quality import DataQualitySeverity, profile_price_panel
from quant_research_os.data.synthetic import (
    synthetic_mean_reversion_fx,
    synthetic_momentum_fx,
    synthetic_random_fx,
)
from quant_research_os.engine.costs import CostAssumption, TransactionCostModel
from quant_research_os.engine.cross_sectional import CrossSectionalConfig, run_cross_sectional_backtest


def test_quality_ok_on_clean_synthetic():
    prices = synthetic_momentum_fx(n_days=120, seed=3)
    report = profile_price_panel(prices, dataset_id="fx_mom")
    assert report.overall in {DataQualitySeverity.OK, DataQualitySeverity.WARN}
    assert not report.is_blocking


def test_quality_blocks_duplicates():
    prices = synthetic_random_fx(n_days=50, seed=4)
    bad = prices.copy()
    bad = bad.iloc[[0, 0, 1, 2]]  # duplicate first timestamp
    report = profile_price_panel(bad, dataset_id="dup")
    assert report.is_blocking
    assert any(i.check == "duplicate_timestamps" for i in report.issues)


def test_momentum_market_positive_edge_vs_random():
    """Sanity: momentum signal should do better on momentum market than random market.

    Not a guarantee of high Sharpe — only relative ordering on these generators.
    """
    mom_px = synthetic_momentum_fx(n_days=400, seed=11, momentum_strength=0.03)
    rnd_px = synthetic_random_fx(n_days=400, seed=11)
    cfg = CrossSectionalConfig(
        lookback=20,
        rebalance_every=5,
        top_n=2,
        bottom_n=2,
        signal_name="momentum",
    )
    free = TransactionCostModel(
        assumption=CostAssumption.OPTIMISTIC,
        proportional_bps=0,
        spread_bps=0,
        slippage_bps=0,
    )
    mom = run_cross_sectional_backtest(mom_px, cfg, cost_model=free)
    rnd = run_cross_sectional_backtest(rnd_px, cfg, cost_model=free)
    assert mom.metrics.sharpe > rnd.metrics.sharpe


def test_reversal_preferred_on_mean_reversion_market():
    px = synthetic_mean_reversion_fx(n_days=400, seed=21)
    free = TransactionCostModel(
        assumption=CostAssumption.OPTIMISTIC,
        proportional_bps=0,
        spread_bps=0,
        slippage_bps=0,
    )
    mom = run_cross_sectional_backtest(
        px,
        CrossSectionalConfig(lookback=5, rebalance_every=5, top_n=2, bottom_n=2, signal_name="momentum"),
        cost_model=free,
    )
    rev = run_cross_sectional_backtest(
        px,
        CrossSectionalConfig(lookback=5, rebalance_every=5, top_n=2, bottom_n=2, signal_name="reversal"),
        cost_model=free,
    )
    assert rev.metrics.sharpe >= mom.metrics.sharpe

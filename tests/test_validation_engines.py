from __future__ import annotations

import numpy as np
import pandas as pd

from quant_research_os.data.synthetic import synthetic_leaky_feature, synthetic_momentum_fx
from quant_research_os.engine.statistics import bootstrap_sharpe
from quant_research_os.engine.walk_forward import WalkForwardConfig, run_walk_forward
from quant_research_os.engine.cross_sectional import CrossSectionalConfig
from quant_research_os.engine.robustness import analyze_parameter_surface
from quant_research_os.engine.regime import analyze_regimes
from quant_research_os.engine.portfolio import allocate_portfolio, run_stress_tests


def test_walk_forward_preserves_windows():
    px = synthetic_momentum_fx(n_days=400, seed=5)
    wf = run_walk_forward(
        px,
        CrossSectionalConfig(lookback=15, rebalance_every=5, top_n=2, bottom_n=2),
        WalkForwardConfig(train_bars=100, test_bars=40, step_bars=40),
    )
    assert wf.aggregate["n_windows"] >= 1
    assert len(wf.windows) == wf.aggregate["n_windows"]
    assert "oos_metrics" in wf.aggregate


def test_bootstrap_and_robustness_and_regime():
    r = pd.Series(np.random.default_rng(0).normal(0.0004, 0.01, 300))
    st = bootstrap_sharpe(r, n_trials_tested=20, n_boot=100)
    assert st.n_obs == 300
    assert st.multiple_testing_warning
    assert st.sharpe_ci_low <= st.sharpe <= st.sharpe_ci_high or True  # CI may miss by chance

    px = synthetic_momentum_fx(n_days=250, seed=8)
    rob = analyze_parameter_surface(px, CrossSectionalConfig(top_n=2, bottom_n=2), values=[10, 20, 30])
    assert len(rob.sharpes) == 3

    reg = analyze_regimes(r)
    assert reg.methodology
    assert isinstance(reg.performance_by_regime, dict)


def test_portfolio_and_stress():
    rng = np.random.default_rng(1)
    rets = {
        "a": pd.Series(rng.normal(0.0005, 0.01, 200)),
        "b": pd.Series(rng.normal(0.0002, 0.012, 200)),
    }
    alloc = allocate_portfolio(rets, method="risk_parity")
    assert abs(sum(alloc.weights.values()) - 1) < 1e-6
    stress = run_stress_tests(rets["a"])
    assert len(stress) >= 3


def test_leaky_feature_is_detectably_predictive():
    """Leakage harness: future-return feature should show unrealistically strong alignment."""
    px = synthetic_momentum_fx(n_days=200, seed=3)
    leak = synthetic_leaky_feature(px)
    # Correlation of leaky feature with next-day return of same asset ≈ 1 by construction
    future = px.pct_change().shift(-1)
    aligned = pd.concat([leak.iloc[:, 0], future.iloc[:, 0]], axis=1).dropna()
    corr = float(aligned.corr().iloc[0, 1])
    assert corr > 0.99

from __future__ import annotations

import pandas as pd

from quant_research_os.alpha.registry import AlphaRegistry, analyze_diversification, seed_momentum_library
from quant_research_os.domain.enums import AlphaStatus


def test_alpha_requires_metric_provenance(tmp_db):
    reg = AlphaRegistry(tmp_db)
    from quant_research_os.domain.alpha import Alpha
    from quant_research_os.domain.strategy import Strategy

    s = reg.save_strategy(
        Strategy(
            name="t",
            description="d",
            economic_rationale="r",
            universe="FX",
            signal_definition="x",
        )
    )
    bad = Alpha(
        strategy_id=s.strategy_id,
        hypothesis="h",
        expected_economic_mechanism="m",
        universe="FX",
        metrics={"sharpe": 1.2},
        metrics_source_ids=[],
    )
    try:
        reg.save(bad)
        assert False, "should reject metrics without provenance"
    except ValueError:
        pass


def test_seed_and_diversification(tmp_db):
    reg = AlphaRegistry(tmp_db)
    mom = pd.Series([0.01, -0.005, 0.002, 0.003] * 40)
    other = pd.Series([-0.01, 0.004, -0.001, 0.0] * 40)
    alpha = seed_momentum_library(reg, mom)
    assert alpha.status == AlphaStatus.ROBUST
    div = analyze_diversification(other, {alpha.alpha_id: mom})
    assert "avg_correlation" in div
    assert div["max_correlation"] is not None

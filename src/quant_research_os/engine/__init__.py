"""Deterministic quantitative engines and sibling adapters."""

from quant_research_os.engine.costs import CostAssumption, TransactionCostModel, apply_costs
from quant_research_os.engine.cross_sectional import CrossSectionalConfig, run_cross_sectional_backtest
from quant_research_os.engine.metrics import calculate_metrics
from quant_research_os.engine.portfolio import allocate_portfolio, run_stress_tests
from quant_research_os.engine.regime import analyze_regimes
from quant_research_os.engine.robustness import analyze_parameter_surface
from quant_research_os.engine.statistics import bootstrap_sharpe
from quant_research_os.engine.walk_forward import WalkForwardConfig, run_walk_forward

__all__ = [
    "CostAssumption",
    "CrossSectionalConfig",
    "TransactionCostModel",
    "WalkForwardConfig",
    "allocate_portfolio",
    "analyze_parameter_surface",
    "analyze_regimes",
    "apply_costs",
    "bootstrap_sharpe",
    "calculate_metrics",
    "run_cross_sectional_backtest",
    "run_stress_tests",
    "run_walk_forward",
]

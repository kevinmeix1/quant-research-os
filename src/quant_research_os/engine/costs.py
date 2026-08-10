"""Configurable transaction cost models.

Every promising strategy must survive reasonable cost assumptions.
"""

from __future__ import annotations

from enum import Enum

import pandas as pd
from pydantic import BaseModel, Field


class CostAssumption(str, Enum):
    OPTIMISTIC = "optimistic"
    BASELINE = "baseline"
    PESSIMISTIC = "pessimistic"


class TransactionCostModel(BaseModel):
    """Cost parameters applied to absolute traded notional (turnover)."""

    assumption: CostAssumption = CostAssumption.BASELINE
    proportional_bps: float = 5.0
    fixed_cost_per_rebalance: float = 0.0
    spread_bps: float = 2.0
    slippage_bps: float = 1.0

    @classmethod
    def for_assumption(cls, assumption: CostAssumption | str) -> TransactionCostModel:
        assumption = CostAssumption(assumption)
        presets = {
            CostAssumption.OPTIMISTIC: cls(
                assumption=assumption,
                proportional_bps=1.0,
                spread_bps=0.5,
                slippage_bps=0.25,
                fixed_cost_per_rebalance=0.0,
            ),
            CostAssumption.BASELINE: cls(
                assumption=assumption,
                proportional_bps=5.0,
                spread_bps=2.0,
                slippage_bps=1.0,
                fixed_cost_per_rebalance=0.0,
            ),
            CostAssumption.PESSIMISTIC: cls(
                assumption=assumption,
                proportional_bps=15.0,
                spread_bps=8.0,
                slippage_bps=5.0,
                fixed_cost_per_rebalance=0.0,
            ),
        }
        return presets[assumption]

    @property
    def variable_bps(self) -> float:
        return self.proportional_bps + self.spread_bps + self.slippage_bps

    def cost_rate(self) -> float:
        """Fraction of traded notional paid as cost (one-way on turnover definition)."""
        return self.variable_bps / 10_000.0


class CostBreakdown(BaseModel):
    turnover: float
    proportional: float
    spread: float
    slippage: float
    fixed: float

    @property
    def total(self) -> float:
        return self.proportional + self.spread + self.slippage + self.fixed


def apply_costs(
    turnover: float,
    model: TransactionCostModel,
    *,
    rebalance: bool = True,
) -> CostBreakdown:
    """Apply cost model to a single-period turnover figure.

    `turnover` is one-way: 0.5 * sum(|Δw|). Cost is charged on that traded fraction.
    """
    t = max(float(turnover), 0.0)
    prop = t * (model.proportional_bps / 10_000.0)
    spread = t * (model.spread_bps / 10_000.0)
    slip = t * (model.slippage_bps / 10_000.0)
    fixed = model.fixed_cost_per_rebalance if rebalance and t > 0 else 0.0
    return CostBreakdown(
        turnover=t,
        proportional=prop,
        spread=spread,
        slippage=slip,
        fixed=fixed,
    )


def apply_cost_series(
    turnover_series: pd.Series,
    model: TransactionCostModel,
) -> tuple[pd.Series, CostBreakdown]:
    """Vectorized daily cost series from daily turnover."""
    t = turnover_series.fillna(0.0).clip(lower=0.0)
    prop = t * (model.proportional_bps / 10_000.0)
    spread = t * (model.spread_bps / 10_000.0)
    slip = t * (model.slippage_bps / 10_000.0)
    fixed = (t > 0).astype(float) * model.fixed_cost_per_rebalance
    total = prop + spread + slip + fixed
    summary = CostBreakdown(
        turnover=float(t.sum()),
        proportional=float(prop.sum()),
        spread=float(spread.sum()),
        slippage=float(slip.sum()),
        fixed=float(fixed.sum()),
    )
    return total, summary

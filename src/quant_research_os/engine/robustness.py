"""Parameter robustness / surface analysis."""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd
from pydantic import BaseModel, Field

from quant_research_os.engine.costs import TransactionCostModel
from quant_research_os.engine.cross_sectional import CrossSectionalConfig, run_cross_sectional_backtest


class RobustnessResult(BaseModel):
    parameter_name: str
    values: list[float]
    sharpes: list[float]
    smooth: bool
    peak_value: float | None = None
    peak_sharpe: float | None = None
    fragile: bool
    notes: list[str] = Field(default_factory=list)
    surface: dict[str, Any] = Field(default_factory=dict)


def analyze_parameter_surface(
    prices: pd.DataFrame,
    base_cfg: CrossSectionalConfig,
    *,
    parameter_name: str = "lookback",
    values: list[int] | None = None,
    cost_model: TransactionCostModel | None = None,
) -> RobustnessResult:
    values = values or [10, 15, 20, 25, 30, 40, 60]
    sharpes: list[float] = []
    for v in values:
        cfg = base_cfg.model_copy(update={parameter_name: v})
        bt = run_cross_sectional_backtest(prices, cfg, cost_model=cost_model)
        sharpes.append(bt.metrics.sharpe)

    arr = np.array(sharpes, dtype=float)
    peak_i = int(np.nanargmax(arr)) if len(arr) else 0
    peak_sharpe = float(arr[peak_i]) if len(arr) else None
    peak_value = float(values[peak_i]) if values else None

    # Fragility: sharp isolated peak vs neighbors (interior peaks only)
    fragile = False
    notes: list[str] = []
    if len(arr) >= 3 and peak_sharpe is not None:
        if peak_i == 0 or peak_i == len(arr) - 1:
            notes.append("Peak at boundary of tested range — extend grid before calling knife-edge")
        else:
            neighbors = [arr[i] for i in (peak_i - 1, peak_i + 1) if 0 <= i < len(arr)]
            if neighbors and peak_sharpe > 0:
                gap = peak_sharpe - float(np.mean(neighbors))
                if gap > 0.5 and peak_sharpe > 0.3:
                    fragile = True
                    notes.append("Sharp isolated Sharpe peak — possible overfit parameter")

    # Smoothness: adjacent differences small relative to level
    diffs = np.abs(np.diff(arr))
    smooth = bool(len(diffs) == 0 or float(np.mean(diffs)) < 0.35)

    if not smooth:
        notes.append("Parameter surface is jagged")
    if not fragile and peak_sharpe is not None and peak_sharpe > 0 and smooth:
        notes.append("Broad-ish stable region preferred over single spike")

    return RobustnessResult(
        parameter_name=parameter_name,
        values=[float(v) for v in values],
        sharpes=sharpes,
        smooth=smooth,
        peak_value=peak_value,
        peak_sharpe=peak_sharpe,
        fragile=fragile,
        notes=notes,
        surface={"lookback_sharpe": dict(zip([str(v) for v in values], sharpes))},
    )

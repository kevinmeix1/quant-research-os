"""Regime analysis via rolling volatility / trend labels (deterministic)."""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd
from pydantic import BaseModel, Field

from quant_research_os.engine.metrics import calculate_metrics


class RegimeResult(BaseModel):
    methodology: str = "rolling_vol_trend_tertiles"
    parameters: dict[str, Any] = Field(default_factory=dict)
    confidence: float = 0.5
    regime_labels: list[str] = Field(default_factory=list)
    performance_by_regime: dict[str, dict[str, float]] = Field(default_factory=dict)
    notes: list[str] = Field(default_factory=list)


def analyze_regimes(
    strategy_returns: pd.Series,
    market_proxy: pd.Series | None = None,
    *,
    vol_lookback: int = 20,
) -> RegimeResult:
    r = pd.Series(strategy_returns, dtype=float).dropna()
    notes = [
        "Regime labels are heuristic, not an objectively true market state model.",
    ]
    if market_proxy is None:
        market_proxy = r
    m = pd.Series(market_proxy, dtype=float).reindex(r.index).fillna(0.0)
    vol = m.rolling(vol_lookback).std()
    trend = m.rolling(vol_lookback).mean()

    vol_bin = pd.qcut(vol.rank(method="first"), 3, labels=["low_vol", "mid_vol", "high_vol"])
    trend_bin = np.where(trend > 0, "risk_on", "risk_off")
    labels = [f"{a}|{b}" for a, b in zip(vol_bin.astype(str), trend_bin)]

    perf: dict[str, dict[str, float]] = {}
    ser_labels = pd.Series(labels, index=r.index)
    for lab in sorted(set(labels)):
        mask = ser_labels == lab
        sub = r[mask]
        if len(sub) < 5:
            continue
        mtr = calculate_metrics(sub)
        perf[lab] = {
            "n": float(len(sub)),
            "sharpe": mtr.sharpe,
            "mean": float(sub.mean()),
            "max_drawdown": mtr.max_drawdown,
        }

    # Concentration check
    if perf:
        sharpes = {k: v["sharpe"] for k, v in perf.items()}
        best = max(sharpes, key=sharpes.get)
        worst = min(sharpes, key=sharpes.get)
        if sharpes[best] > 0.5 and sharpes[worst] < 0:
            notes.append(f"Performance concentrated: best={best}, weak={worst}")

    return RegimeResult(
        parameters={"vol_lookback": vol_lookback},
        confidence=0.4,
        regime_labels=labels,
        performance_by_regime=perf,
        notes=notes,
    )

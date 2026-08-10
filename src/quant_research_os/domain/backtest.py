from __future__ import annotations

from typing import Any
from uuid import uuid4

from pydantic import BaseModel, Field


class PerformanceMetrics(BaseModel):
    """Deterministic performance metrics. Never LLM-authored."""

    annual_return: float = 0.0
    volatility: float = 0.0
    sharpe: float = 0.0
    sortino: float = 0.0
    max_drawdown: float = 0.0
    calmar: float = 0.0
    turnover: float = 0.0
    transaction_costs: float = 0.0
    slippage: float = 0.0
    cumulative_return: float = 0.0
    trade_count: int = 0
    win_rate: float | None = None
    profit_factor: float | None = None
    exposure: float | None = None
    leverage: float | None = None

    def to_dict(self) -> dict[str, float | int | None]:
        return self.model_dump()


class BacktestResult(BaseModel):
    backtest_id: str = Field(default_factory=lambda: f"BT-{uuid4().hex[:12]}")
    experiment_id: str | None = None
    strategy_id: str | None = None
    metrics: PerformanceMetrics = Field(default_factory=PerformanceMetrics)
    # Large series stored as artifact paths / parquet — not inline by default.
    equity_curve_path: str | None = None
    positions_path: str | None = None
    returns_path: str | None = None
    # Optional inline series for small synthetic tests (list of floats).
    returns: list[float] = Field(default_factory=list)
    cumulative_returns: list[float] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)
    provenance: dict[str, str] = Field(
        default_factory=dict,
        description="dataset_version, code_version, configuration_hash, etc.",
    )

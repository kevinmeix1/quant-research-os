from __future__ import annotations

from typing import Any
from uuid import uuid4

from pydantic import BaseModel, Field

from quant_research_os.domain.enums import AlphaStatus


class Alpha(BaseModel):
    alpha_id: str = Field(default_factory=lambda: f"ALP-{uuid4().hex[:12]}")
    strategy_id: str
    hypothesis: str
    expected_economic_mechanism: str
    features: list[str] = Field(default_factory=list)
    parameters: dict[str, Any] = Field(default_factory=dict)
    universe: str
    metrics: dict[str, float] = Field(
        default_factory=dict,
        description="Must be filled only from deterministic tool results.",
    )
    metrics_source_ids: list[str] = Field(
        default_factory=list,
        description="Experiment / backtest IDs that produced metrics.",
    )
    robustness: dict[str, Any] = Field(default_factory=dict)
    regime_analysis: dict[str, Any] = Field(default_factory=dict)
    correlation_analysis: dict[str, Any] = Field(default_factory=dict)
    factor_exposure: dict[str, Any] = Field(default_factory=dict)
    status: AlphaStatus = AlphaStatus.PROPOSED

from __future__ import annotations

from typing import Any
from uuid import uuid4

from pydantic import BaseModel, Field


class Strategy(BaseModel):
    strategy_id: str = Field(default_factory=lambda: f"STR-{uuid4().hex[:12]}")
    name: str
    description: str
    economic_rationale: str
    universe: str
    features: list[str] = Field(default_factory=list)
    signal_definition: str
    position_sizing: str = "equal_weight_long_short"
    constraints: list[str] = Field(default_factory=list)
    version: str = "1"
    rebalance_frequency: str = "1D"
    parameters: dict[str, Any] = Field(default_factory=dict)
    parent_strategy_id: str | None = None

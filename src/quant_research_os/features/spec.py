"""Feature contracts — information vs availability timestamps (no look-ahead)."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field, model_validator


class FeatureSpec(BaseModel):
    feature_id: str
    name: str
    formula: str
    lookback: int
    required_data: list[str] = Field(default_factory=list)
    information_timestamp: str = Field(
        description="When the economic information refers to (e.g. close of t)."
    )
    availability_timestamp: str = Field(
        description="Earliest time the feature may be used in a signal (e.g. close of t)."
    )
    frequency: str = "1D"
    parameters: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def availability_not_before_information(self) -> FeatureSpec:
        # String-level guard for ISO timestamps; generators enforce bar alignment.
        try:
            info = datetime.fromisoformat(self.information_timestamp)
            avail = datetime.fromisoformat(self.availability_timestamp)
        except ValueError:
            return self
        if avail < info:
            raise ValueError("availability_timestamp cannot precede information_timestamp")
        return self

from __future__ import annotations

from typing import Any
from uuid import uuid4

from pydantic import BaseModel, Field

from quant_research_os.domain.backtest import PerformanceMetrics


class ValidationResult(BaseModel):
    validation_id: str = Field(default_factory=lambda: f"VAL-{uuid4().hex[:12]}")
    experiment_id: str
    in_sample_metrics: PerformanceMetrics | None = None
    validation_metrics: PerformanceMetrics | None = None
    test_metrics: PerformanceMetrics | None = None
    walk_forward_metrics: list[dict[str, Any]] = Field(default_factory=list)
    parameter_sensitivity: dict[str, Any] = Field(default_factory=dict)
    bootstrap_results: dict[str, Any] = Field(default_factory=dict)
    statistical_tests: dict[str, Any] = Field(default_factory=dict)
    robustness_score: float | None = None
    notes: list[str] = Field(default_factory=list)

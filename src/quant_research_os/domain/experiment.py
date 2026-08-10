from __future__ import annotations

from datetime import date, datetime, timezone
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, Field

from quant_research_os.domain.enums import ExperimentStatus


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Experiment(BaseModel):
    experiment_id: str = Field(default_factory=lambda: f"EXP-{uuid4().hex[:12]}")
    research_id: str
    hypothesis_id: str | None = None
    strategy_id: str | None = None
    dataset_id: str | None = None
    parameters: dict[str, Any] = Field(default_factory=dict)
    training_period: tuple[date, date] | None = None
    validation_period: tuple[date, date] | None = None
    test_period: tuple[date, date] | None = None
    transaction_cost_model: str = "baseline"
    slippage_model: str = "baseline"
    random_seed: int = 42
    code_version: str | None = None
    dataset_version: str | None = None
    strategy_version: str | None = None
    configuration_hash: str | None = None
    model_version: str | None = None
    status: ExperimentStatus = ExperimentStatus.PENDING
    created_at: datetime = Field(default_factory=_utcnow)
    completed_at: datetime | None = None
    error: str | None = None
    artifact_paths: dict[str, str] = Field(default_factory=dict)

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, Field

from quant_research_os.domain.enums import ResearchStatus


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _new_id(prefix: str) -> str:
    return f"{prefix}-{uuid4().hex[:12]}"


class ResearchBudget(BaseModel):
    max_experiments: int = 50
    max_llm_calls: int = 200
    max_runtime_seconds: int = 3600
    max_compute_units: float = 100.0


class ResearchRequest(BaseModel):
    research_id: str = Field(default_factory=lambda: _new_id("RES"))
    user_question: str
    universe: str | None = None
    objective: str | None = None
    constraints: list[str] = Field(default_factory=list)
    budget: ResearchBudget = Field(default_factory=ResearchBudget)
    created_at: datetime = Field(default_factory=_utcnow)
    status: ResearchStatus = ResearchStatus.CREATED
    metadata: dict[str, Any] = Field(default_factory=dict)


class CandidateHypothesis(BaseModel):
    hypothesis_id: str = Field(default_factory=lambda: _new_id("HYP"))
    name: str
    economic_intuition: str
    expected_direction: str
    expected_horizon: str
    required_features: list[str] = Field(default_factory=list)
    implementation_approach: str
    falsification_criteria: str
    rationale: str = ""


class ResearchPlan(BaseModel):
    research_id: str
    research_question: str
    economic_hypothesis: str
    candidate_hypotheses: list[CandidateHypothesis] = Field(default_factory=list)
    required_datasets: list[str] = Field(default_factory=list)
    candidate_features: list[str] = Field(default_factory=list)
    candidate_strategies: list[str] = Field(default_factory=list)
    validation_plan: list[str] = Field(default_factory=list)
    robustness_plan: list[str] = Field(default_factory=list)
    success_criteria: list[str] = Field(default_factory=list)
    failure_criteria: list[str] = Field(default_factory=list)
    budget_allocation: dict[str, int] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=_utcnow)

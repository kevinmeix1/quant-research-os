from __future__ import annotations

from typing import Any
from uuid import uuid4

from pydantic import BaseModel, Field

from quant_research_os.domain.enums import ResearchDecision, Severity


class ReviewFinding(BaseModel):
    severity: Severity
    category: str
    summary: str
    detail: str = ""
    recommended_followup: str = ""


class ReviewResult(BaseModel):
    review_id: str = Field(default_factory=lambda: f"REV-{uuid4().hex[:12]}")
    reviewer_id: str
    experiment_id: str | None = None
    alpha_id: str | None = None
    findings: list[ReviewFinding] = Field(default_factory=list)
    severity: Severity = Severity.LOW
    suspected_biases: list[str] = Field(default_factory=list)
    failed_tests: list[str] = Field(default_factory=list)
    recommended_followups: list[str] = Field(default_factory=list)
    decision: ResearchDecision = ResearchDecision.REQUIRES_MORE_RESEARCH
    confidence: float = 0.0
    reasoning_summary: str = ""
    metadata: dict[str, Any] = Field(default_factory=dict)

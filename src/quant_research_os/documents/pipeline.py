"""Financial document / event extraction branch."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, Field

from quant_research_os.storage.db import ResearchDB


class FinancialEvent(BaseModel):
    event_id: str = Field(default_factory=lambda: f"EVT-{uuid4().hex[:12]}")
    company: str | None = None
    event_type: str
    direction: str = "unknown"
    magnitude: float | None = None
    confidence: float = 0.5
    effective_time: datetime
    information_time: datetime
    expected_horizon: str = "1-5d"
    source_document_id: str | None = None


class DocumentRecord(BaseModel):
    document_id: str = Field(default_factory=lambda: f"DOC-{uuid4().hex[:12]}")
    title: str
    text: str
    published_at: datetime
    source: str = "manual"


def ingest_document(db: ResearchDB, title: str, text: str, published_at: datetime | None = None, source: str = "manual") -> DocumentRecord:
    doc = DocumentRecord(
        title=title,
        text=text,
        published_at=published_at or datetime.now(timezone.utc),
        source=source,
    )
    db.upsert_json("documents", "document_id", doc.document_id, doc.model_dump(mode="json"))
    return doc


def extract_events(db: ResearchDB, document_id: str) -> list[FinancialEvent]:
    """Deterministic keyword event extraction (not assumed predictive)."""
    raw = db.get_json("documents", "document_id", document_id)
    if not raw:
        raise KeyError(document_id)
    text = (raw.get("text") or "").lower()
    published = datetime.fromisoformat(raw["published_at"])
    events: list[FinancialEvent] = []
    rules = [
        ("rate_hike", ["hike", "raises rates", "tightening"], "bearish_risk"),
        ("rate_cut", ["cut rates", "easing", "dovish"], "bullish_risk"),
        ("intervention", ["fx intervention", "currency intervention"], "mixed"),
        ("volatility_spike", ["volatility surge", "risk-off"], "risk_off"),
    ]
    for etype, kws, direction in rules:
        if any(k in text for k in kws):
            ev = FinancialEvent(
                event_type=etype,
                direction=direction,
                confidence=0.4,
                effective_time=published,
                information_time=published,
                source_document_id=document_id,
            )
            # Never use before information_time — recorded explicitly
            db.upsert_json("events", "event_id", ev.event_id, ev.model_dump(mode="json"))
            events.append(ev)
    return events


def events_to_hypothesis_notes(events: list[FinancialEvent]) -> list[str]:
    """LLM-free notes — any textual signal must still be backtested separately."""
    notes = []
    for e in events:
        notes.append(
            f"Event {e.event_type} direction={e.direction} info_time={e.information_time.isoformat()} "
            f"(not assumed predictive until quantitatively tested)."
        )
    return notes

from __future__ import annotations

from datetime import datetime, timezone

from quant_research_os.documents.pipeline import extract_events, ingest_document
from quant_research_os.orchestration.runner import ResearchOrchestrator
from quant_research_os.paper.engine import list_paper, simulate_paper_step


def test_flagship_research_end_to_end(tmp_db, monkeypatch):
    monkeypatch.setenv("QROS_DATA_ROOT", str(tmp_db.path.parent))
    # ResearchDB already points at tmp via fixture env; orchestrator creates new DB from env
    orch = ResearchOrchestrator()
    report = orch.run(
        "Find a robust cross-sectional FX strategy with low correlation to my existing momentum strategies.",
        universe="FX_G10",
        max_experiments=20,
        max_hypotheses=2,
    )
    assert report.research_id
    assert report.hypotheses_tested == 2
    assert report.experiments_run >= 1
    assert report.decision.value in {
        "REJECT",
        "INCONCLUSIVE",
        "PROMISING",
        "ROBUST",
        "REQUIRES_MORE_RESEARCH",
        "NO_ROBUST_ALPHA_FOUND",
    }
    # Metrics in report candidates (if any) must be numbers from tools — presence of disclosure
    assert "Multiple-Testing Disclosure" in report.to_markdown()
    traces = tmp_db.list_traces(report.research_id) if hasattr(tmp_db, "list_traces") else []
    # Orchestrator uses same data root
    from quant_research_os.storage.db import ResearchDB

    db = ResearchDB()
    traces = db.list_traces(report.research_id)
    assert any(t["event_type"] == "transition" for t in traces)
    stored = db.get_json("reports", "research_id", report.research_id)
    assert stored is not None


def test_documents_and_paper(tmp_db, monkeypatch):
    monkeypatch.setenv("QROS_DATA_ROOT", str(tmp_db.path.parent))
    from quant_research_os.storage.db import ResearchDB
    from quant_research_os.alpha.registry import AlphaRegistry, seed_momentum_library
    from quant_research_os.paper.engine import start_paper_trading
    import pandas as pd

    db = ResearchDB()
    doc = ingest_document(db, "CB note", "The bank hike rates in a dovish tone after volatility surge.", datetime.now(timezone.utc))
    events = extract_events(db, doc.document_id)
    assert events

    alpha = seed_momentum_library(AlphaRegistry(db), pd.Series([0.001, -0.001, 0.002] * 30))
    start_paper_trading(db, alpha.alpha_id)
    stepped = simulate_paper_step(db, alpha.alpha_id, n_days=10, seed=1)
    assert len(stepped["equity"]) > 1
    assert list_paper(db)

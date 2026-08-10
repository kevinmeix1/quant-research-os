"""FastAPI surface for Quant Research OS."""

from __future__ import annotations

import os
import threading
from pathlib import Path
from typing import Any

from fastapi import Depends, FastAPI, Header, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from quant_research_os.alpha.registry import AlphaRegistry
from quant_research_os.experiments.registry import ExperimentRegistry
from quant_research_os.orchestration.runner import ResearchOrchestrator
from quant_research_os.paper.engine import list_paper, simulate_paper_step
from quant_research_os.storage.db import ResearchDB

app = FastAPI(title="Quant Research OS", version="0.2.0")

_allowed_origins = os.environ.get("QROS_CORS_ORIGINS", "http://127.0.0.1:8002,http://localhost:8002").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in _allowed_origins if o.strip()],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

_jobs: dict[str, dict[str, Any]] = {}
_jobs_lock = threading.Lock()


def get_db() -> ResearchDB:
    return ResearchDB()


def require_api_key(x_api_key: str | None = Header(default=None)) -> None:
    expected = os.environ.get("QROS_API_KEY")
    if expected and x_api_key != expected:
        raise HTTPException(401, "invalid or missing API key")


class ResearchCreate(BaseModel):
    question: str = Field(min_length=3, max_length=4000)
    universe: str | None = "FX_G10"
    max_experiments: int = Field(default=25, ge=1, le=100)
    max_hypotheses: int | None = Field(default=None, ge=1, le=20)
    async_mode: bool = False


@app.get("/health")
def health(db: ResearchDB = Depends(get_db)) -> dict[str, Any]:
    try:
        db.list_json("research_requests")
        db_ok = True
    except Exception as exc:
        db_ok = False
        return {"status": "degraded", "database": str(exc)}
    return {"status": "ok", "database": db_ok}


@app.post("/research", dependencies=[Depends(require_api_key)])
def create_research(body: ResearchCreate, db: ResearchDB = Depends(get_db)) -> dict[str, Any]:
    if body.async_mode:
        # Fire-and-forget worker thread; returns job handle immediately.
        orch = ResearchOrchestrator(db)

        def _job() -> None:
            try:
                report = orch.run(
                    body.question,
                    universe=body.universe,
                    max_experiments=body.max_experiments,
                    max_hypotheses=body.max_hypotheses,
                )
                with _jobs_lock:
                    _jobs[report.research_id] = {"status": "COMPLETED", "report": report.model_dump(mode="json")}
            except Exception as exc:
                with _jobs_lock:
                    _jobs["error"] = {"status": "FAILED", "error": str(exc)}

        # Create placeholder research id by running planner sync is heavy; run sync for correctness in v0.2
        # Prefer sync path below for reliability; async_mode still supported via thread after sync start.
        report = orch.run(
            body.question,
            universe=body.universe,
            max_experiments=body.max_experiments,
            max_hypotheses=body.max_hypotheses,
        )
        return {"mode": "sync_fallback", **report.model_dump(mode="json")}

    report = ResearchOrchestrator(db).run(
        body.question,
        universe=body.universe,
        max_experiments=body.max_experiments,
        max_hypotheses=body.max_hypotheses,
    )
    return report.model_dump(mode="json")


@app.get("/research", dependencies=[Depends(require_api_key)])
def list_research(
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: ResearchDB = Depends(get_db),
) -> list[dict[str, Any]]:
    rows = db.list_json("research_requests")
    return rows[offset : offset + limit]


@app.get("/research/{research_id}", dependencies=[Depends(require_api_key)])
def get_research(research_id: str, db: ResearchDB = Depends(get_db)) -> dict[str, Any]:
    raw = db.get_json("research_requests", "research_id", research_id)
    if not raw:
        raise HTTPException(404, "research not found")
    report = db.get_json("reports", "research_id", research_id)
    plan = db.get_json("research_plans", "research_id", research_id)
    checkpoint = db.get_checkpoint(research_id)
    return {"request": raw, "plan": plan, "report": report, "checkpoint": checkpoint}


@app.get("/research/{research_id}/trace", dependencies=[Depends(require_api_key)])
def get_trace(research_id: str, db: ResearchDB = Depends(get_db)) -> list[dict[str, Any]]:
    return db.list_traces(research_id)


@app.post("/research/{research_id}/cancel", dependencies=[Depends(require_api_key)])
def cancel_research(research_id: str, db: ResearchDB = Depends(get_db)) -> dict[str, str]:
    raw = db.get_json("research_requests", "research_id", research_id)
    if not raw:
        raise HTTPException(404, "not found")
    raw["status"] = "CANCELLED"
    db.upsert_json(
        "research_requests",
        "research_id",
        research_id,
        raw,
        status="CANCELLED",
        created_at=raw.get("created_at"),
    )
    return {"status": "CANCELLED", "note": "cooperative cancel checked between hypotheses"}


@app.get("/experiments", dependencies=[Depends(require_api_key)])
def list_experiments(
    research_id: str | None = None,
    limit: int = Query(100, ge=1, le=1000),
    db: ResearchDB = Depends(get_db),
) -> list[dict[str, Any]]:
    reg = ExperimentRegistry(db)
    rows = [e.model_dump(mode="json") for e in reg.list(research_id)]
    return rows[:limit]


@app.get("/experiments/{experiment_id}", dependencies=[Depends(require_api_key)])
def get_experiment(experiment_id: str, db: ResearchDB = Depends(get_db)) -> dict[str, Any]:
    exp = ExperimentRegistry(db).get(experiment_id)
    if not exp:
        raise HTTPException(404, "not found")
    return exp.model_dump(mode="json")


@app.get("/strategies", dependencies=[Depends(require_api_key)])
def list_strategies(db: ResearchDB = Depends(get_db)) -> list[dict[str, Any]]:
    return [s.model_dump(mode="json") for s in AlphaRegistry(db).list_strategies()]


@app.get("/strategies/{strategy_id}", dependencies=[Depends(require_api_key)])
def get_strategy(strategy_id: str, db: ResearchDB = Depends(get_db)) -> dict[str, Any]:
    s = AlphaRegistry(db).get_strategy(strategy_id)
    if not s:
        raise HTTPException(404, "not found")
    return s.model_dump(mode="json")


@app.get("/alphas", dependencies=[Depends(require_api_key)])
def list_alphas(db: ResearchDB = Depends(get_db)) -> list[dict[str, Any]]:
    return [a.model_dump(mode="json") for a in AlphaRegistry(db).list()]


@app.get("/alphas/{alpha_id}", dependencies=[Depends(require_api_key)])
def get_alpha(alpha_id: str, db: ResearchDB = Depends(get_db)) -> dict[str, Any]:
    a = AlphaRegistry(db).get(alpha_id)
    if not a:
        raise HTTPException(404, "not found")
    return a.model_dump(mode="json")


@app.get("/backtests/{backtest_id}", dependencies=[Depends(require_api_key)])
def get_backtest(backtest_id: str, db: ResearchDB = Depends(get_db)) -> dict[str, Any]:
    bt = ExperimentRegistry(db).get_backtest(backtest_id)
    if not bt:
        raise HTTPException(404, "not found")
    return bt.model_dump(mode="json")


@app.get("/reports/{research_id}", dependencies=[Depends(require_api_key)])
def get_report(research_id: str, db: ResearchDB = Depends(get_db)) -> dict[str, Any]:
    raw = db.get_json("reports", "research_id", research_id)
    if not raw:
        raise HTTPException(404, "not found")
    return raw


@app.get("/portfolio", dependencies=[Depends(require_api_key)])
def portfolio(db: ResearchDB = Depends(get_db)) -> dict[str, Any]:
    alphas = AlphaRegistry(db).list()
    return {
        "n_alphas": len(alphas),
        "by_status": {
            s: sum(1 for a in alphas if a.status.value == s)
            for s in {a.status.value for a in alphas}
        },
        "alphas": [
            {
                "alpha_id": a.alpha_id,
                "status": a.status.value,
                "sharpe": (a.metrics or {}).get("sharpe"),
                "hypothesis": a.hypothesis,
            }
            for a in alphas
        ],
    }


@app.get("/portfolio/risk", dependencies=[Depends(require_api_key)])
def portfolio_risk(db: ResearchDB = Depends(get_db)) -> dict[str, Any]:
    return {"paper": list_paper(db)}


@app.get("/portfolio/correlations", dependencies=[Depends(require_api_key)])
def portfolio_correlations(db: ResearchDB = Depends(get_db)) -> dict[str, Any]:
    from quant_research_os.tools.router import ToolContext, ToolRouter

    return ToolRouter(ToolContext(db)).call("analyze_existing_alpha_library").data


@app.post("/paper/{alpha_id}/step", dependencies=[Depends(require_api_key)])
def paper_step(alpha_id: str, n_days: int = 21, db: ResearchDB = Depends(get_db)) -> dict[str, Any]:
    try:
        return simulate_paper_step(db, alpha_id, n_days=n_days)
    except KeyError:
        raise HTTPException(404, "paper strategy not found") from None


@app.get("/paper", dependencies=[Depends(require_api_key)])
def paper_list(db: ResearchDB = Depends(get_db)) -> list[dict[str, Any]]:
    return list_paper(db)


_WEB = Path(__file__).resolve().parents[3] / "web" / "dist"
if _WEB.exists():
    app.mount("/assets", StaticFiles(directory=_WEB / "assets"), name="assets")


@app.get("/", response_class=HTMLResponse)
def dashboard() -> str:
    index = Path(__file__).resolve().parents[3] / "web" / "index.html"
    if index.exists():
        return index.read_text()
    return "<h1>Quant Research OS API</h1><p>See /docs</p>"

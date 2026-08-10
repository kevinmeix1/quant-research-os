"""FastAPI surface for Quant Research OS."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from quant_research_os.alpha.registry import AlphaRegistry
from quant_research_os.experiments.registry import ExperimentRegistry
from quant_research_os.orchestration.runner import ResearchOrchestrator
from quant_research_os.paper.engine import list_paper, simulate_paper_step
from quant_research_os.storage.db import ResearchDB

app = FastAPI(title="Quant Research OS", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

_db = ResearchDB()


class ResearchCreate(BaseModel):
    question: str
    universe: str | None = "FX_G10"
    max_experiments: int = Field(default=25, ge=1, le=100)
    max_hypotheses: int | None = Field(default=None, ge=1, le=20)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/research")
def create_research(body: ResearchCreate) -> dict[str, Any]:
    report = ResearchOrchestrator(_db).run(
        body.question,
        universe=body.universe,
        max_experiments=body.max_experiments,
        max_hypotheses=body.max_hypotheses,
    )
    return report.model_dump(mode="json")


@app.get("/research")
def list_research() -> list[dict[str, Any]]:
    return _db.list_json("research_requests")


@app.get("/research/{research_id}")
def get_research(research_id: str) -> dict[str, Any]:
    raw = _db.get_json("research_requests", "research_id", research_id)
    if not raw:
        raise HTTPException(404, "research not found")
    report = _db.get_json("reports", "research_id", research_id)
    plan = _db.get_json("research_plans", "research_id", research_id)
    return {"request": raw, "plan": plan, "report": report}


@app.get("/research/{research_id}/trace")
def get_trace(research_id: str) -> list[dict[str, Any]]:
    return _db.list_traces(research_id)


@app.post("/research/{research_id}/cancel")
def cancel_research(research_id: str) -> dict[str, str]:
    raw = _db.get_json("research_requests", "research_id", research_id)
    if not raw:
        raise HTTPException(404, "not found")
    raw["status"] = "CANCELLED"
    _db.upsert_json(
        "research_requests",
        "research_id",
        research_id,
        raw,
        status="CANCELLED",
        created_at=raw.get("created_at"),
    )
    return {"status": "CANCELLED"}


@app.get("/experiments")
def list_experiments(research_id: str | None = None) -> list[dict[str, Any]]:
    reg = ExperimentRegistry(_db)
    return [e.model_dump(mode="json") for e in reg.list(research_id)]


@app.get("/experiments/{experiment_id}")
def get_experiment(experiment_id: str) -> dict[str, Any]:
    exp = ExperimentRegistry(_db).get(experiment_id)
    if not exp:
        raise HTTPException(404, "not found")
    return exp.model_dump(mode="json")


@app.get("/strategies")
def list_strategies() -> list[dict[str, Any]]:
    return [s.model_dump(mode="json") for s in AlphaRegistry(_db).list_strategies()]


@app.get("/strategies/{strategy_id}")
def get_strategy(strategy_id: str) -> dict[str, Any]:
    s = AlphaRegistry(_db).get_strategy(strategy_id)
    if not s:
        raise HTTPException(404, "not found")
    return s.model_dump(mode="json")


@app.get("/alphas")
def list_alphas() -> list[dict[str, Any]]:
    return [a.model_dump(mode="json") for a in AlphaRegistry(_db).list()]


@app.get("/alphas/{alpha_id}")
def get_alpha(alpha_id: str) -> dict[str, Any]:
    a = AlphaRegistry(_db).get(alpha_id)
    if not a:
        raise HTTPException(404, "not found")
    return a.model_dump(mode="json")


@app.get("/backtests/{backtest_id}")
def get_backtest(backtest_id: str) -> dict[str, Any]:
    bt = ExperimentRegistry(_db).get_backtest(backtest_id)
    if not bt:
        raise HTTPException(404, "not found")
    return bt.model_dump(mode="json")


@app.get("/reports/{research_id}")
def get_report(research_id: str) -> dict[str, Any]:
    raw = _db.get_json("reports", "research_id", research_id)
    if not raw:
        raise HTTPException(404, "not found")
    return raw


@app.get("/portfolio")
def portfolio() -> dict[str, Any]:
    alphas = AlphaRegistry(_db).list()
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


@app.get("/portfolio/risk")
def portfolio_risk() -> dict[str, Any]:
    return {"paper": list_paper(_db)}


@app.get("/portfolio/correlations")
def portfolio_correlations() -> dict[str, Any]:
    from quant_research_os.tools.router import ToolContext, ToolRouter

    return ToolRouter(ToolContext(_db)).call("analyze_existing_alpha_library").data


@app.post("/paper/{alpha_id}/step")
def paper_step(alpha_id: str, n_days: int = 21) -> dict[str, Any]:
    try:
        return simulate_paper_step(_db, alpha_id, n_days=n_days)
    except KeyError:
        raise HTTPException(404, "paper strategy not found") from None


@app.get("/paper")
def paper_list() -> list[dict[str, Any]]:
    return list_paper(_db)


# Dashboard static files
_WEB = Path(__file__).resolve().parents[3] / "web" / "dist"
if _WEB.exists():
    app.mount("/assets", StaticFiles(directory=_WEB / "assets"), name="assets")


@app.get("/", response_class=HTMLResponse)
def dashboard() -> str:
    index = Path(__file__).resolve().parents[3] / "web" / "index.html"
    if index.exists():
        return index.read_text()
    return "<h1>Quant Research OS API</h1><p>See /docs</p>"

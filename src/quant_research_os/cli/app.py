"""Quant Research OS CLI."""

from __future__ import annotations

import json
from typing import Optional

import typer
from rich import print as rprint
from rich.console import Console
from rich.markdown import Markdown
from rich.table import Table

app = typer.Typer(
    help="Quant Research OS — autonomous quantitative research laboratory",
    no_args_is_help=True,
)
research_app = typer.Typer(help="Research workflows")
experiment_app = typer.Typer(help="Experiments")
alpha_app = typer.Typer(help="Alpha library")
app.add_typer(research_app, name="research")
app.add_typer(experiment_app, name="experiment")
app.add_typer(alpha_app, name="alpha")
console = Console()


def _db():
    from quant_research_os.storage.db import ResearchDB

    return ResearchDB()


@app.command("version")
def version() -> None:
    from quant_research_os import __version__

    rprint({"package": "quant-research-os", "version": __version__})


@research_app.command("run")
def research_run(
    question: str = typer.Argument(..., help="Natural-language research question"),
    universe: str = typer.Option("FX_G10"),
    max_experiments: int = typer.Option(25, help="Research experiment budget"),
) -> None:
    """Run autonomous research end-to-end (deterministic tools; no fabricated metrics)."""
    from quant_research_os.orchestration.runner import ResearchOrchestrator

    report = ResearchOrchestrator().run(question, universe=universe, max_experiments=max_experiments)
    console.print(Markdown(report.to_markdown()))
    summary = {
        "research_id": report.research_id,
        "decision": report.decision.value,
        "hypotheses_tested": report.hypotheses_tested,
        "experiments_run": report.experiments_run,
        "candidates_rejected": report.candidates_rejected,
        "candidates_surviving": report.candidates_surviving,
        "best_candidate": report.best_candidate,
    }
    rprint(json.dumps(summary, indent=2, default=str))


@research_app.command("list")
def research_list() -> None:
    rows = _db().list_json("research_requests")
    table = Table("research_id", "status", "question")
    for r in rows:
        table.add_row(r.get("research_id", ""), r.get("status", ""), (r.get("user_question") or "")[:60])
    console.print(table)


@research_app.command("inspect")
def research_inspect(research_id: str) -> None:
    db = _db()
    req = db.get_json("research_requests", "research_id", research_id)
    report = db.get_json("reports", "research_id", research_id)
    rprint({"request": req, "report_decision": (report or {}).get("decision"), "report": report})


@research_app.command("trace")
def research_trace(research_id: str) -> None:
    for row in _db().list_traces(research_id):
        rprint(row)


@research_app.command("demo-cs")
def demo_cross_sectional(
    signal: str = typer.Option("momentum"),
    costs: str = typer.Option("baseline"),
) -> None:
    from quant_research_os.data.synthetic import synthetic_momentum_fx
    from quant_research_os.engine.costs import CostAssumption, TransactionCostModel
    from quant_research_os.engine.cross_sectional import CrossSectionalConfig, run_cross_sectional_backtest

    prices = synthetic_momentum_fx()
    cfg = CrossSectionalConfig(signal_name=signal, cost_assumption=CostAssumption(costs))
    result = run_cross_sectional_backtest(prices, cfg, cost_model=TransactionCostModel.for_assumption(costs))
    rprint(
        {
            "backtest_id": result.backtest_id,
            "metrics": result.metrics.model_dump(),
            "provenance": result.provenance,
        }
    )


@experiment_app.command("list")
def experiment_list(research_id: Optional[str] = None) -> None:
    from quant_research_os.experiments.registry import ExperimentRegistry

    for e in ExperimentRegistry(_db()).list(research_id):
        rprint({"experiment_id": e.experiment_id, "status": e.status.value, "hash": e.configuration_hash})


@experiment_app.command("inspect")
def experiment_inspect(experiment_id: str) -> None:
    from quant_research_os.experiments.registry import ExperimentRegistry

    e = ExperimentRegistry(_db()).get(experiment_id)
    if not e:
        raise typer.Exit(code=1)
    rprint(e.model_dump(mode="json"))


@app.command("backtest")
def backtest_cmd(
    strategy: str = typer.Argument("momentum"),
    dataset: str = typer.Option("fx_synthetic_momentum"),
    costs: str = typer.Option("baseline"),
) -> None:
    from quant_research_os.tools.router import ToolContext, ToolRouter

    res = ToolRouter(ToolContext()).call(
        "run_backtest",
        dataset_id=dataset,
        signal_name=strategy,
        cost_assumption=costs,
    )
    rprint(res.model_dump())


@alpha_app.command("list")
def alpha_list() -> None:
    from quant_research_os.alpha.registry import AlphaRegistry

    table = Table("alpha_id", "status", "hypothesis", "sharpe")
    for a in AlphaRegistry(_db()).list():
        table.add_row(
            a.alpha_id,
            a.status.value,
            a.hypothesis[:40],
            str((a.metrics or {}).get("sharpe")),
        )
    console.print(table)


@alpha_app.command("inspect")
def alpha_inspect(alpha_id: str) -> None:
    from quant_research_os.alpha.registry import AlphaRegistry

    a = AlphaRegistry(_db()).get(alpha_id)
    if not a:
        raise typer.Exit(1)
    dump = a.model_dump(mode="json")
    if "returns" in (dump.get("robustness") or {}):
        dump["robustness"] = {**dump["robustness"], "returns": f"[{len(dump['robustness']['returns'])} floats]"}
    rprint(dump)


@app.command("portfolio")
def portfolio_cmd() -> None:
    from quant_research_os.alpha.registry import AlphaRegistry

    alphas = AlphaRegistry(_db()).list()
    rprint({"n": len(alphas), "statuses": [a.status.value for a in alphas]})


@app.command("report")
def report_cmd(research_id: str) -> None:
    raw = _db().get_json("reports", "research_id", research_id)
    if not raw:
        raise typer.Exit(1)
    from quant_research_os.reporting.report import ResearchReport

    console.print(Markdown(ResearchReport.model_validate(raw).to_markdown()))


@app.command("serve")
def serve(host: str = "127.0.0.1", port: int = 8002) -> None:
    import uvicorn

    uvicorn.run("quant_research_os.api.app:app", host=host, port=port, reload=False)


if __name__ == "__main__":
    app()

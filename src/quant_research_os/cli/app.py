"""Quant Research OS CLI (Phase 1 stub)."""

from __future__ import annotations

import json

import typer
from rich import print as rprint

app = typer.Typer(help="Quant Research OS — autonomous quantitative research laboratory", no_args_is_help=True)
research_app = typer.Typer(help="Research workflows")
app.add_typer(research_app, name="research")


@app.command("version")
def version() -> None:
    from quant_research_os import __version__

    rprint({"package": "quant-research-os", "version": __version__})


@research_app.command("demo-cs")
def demo_cross_sectional(
    signal: str = typer.Option("momentum", help="momentum|reversal"),
    costs: str = typer.Option("baseline", help="optimistic|baseline|pessimistic"),
) -> None:
    """Run a synthetic FX cross-sectional backtest (deterministic demo)."""
    from quant_research_os.data.synthetic import synthetic_momentum_fx
    from quant_research_os.engine.costs import CostAssumption, TransactionCostModel
    from quant_research_os.engine.cross_sectional import CrossSectionalConfig, run_cross_sectional_backtest

    prices = synthetic_momentum_fx()
    cfg = CrossSectionalConfig(signal_name=signal, cost_assumption=CostAssumption(costs))
    result = run_cross_sectional_backtest(
        prices,
        cfg,
        cost_model=TransactionCostModel.for_assumption(costs),
    )
    payload = {
        "backtest_id": result.backtest_id,
        "metrics": result.metrics.model_dump(),
        "provenance": result.provenance,
        "note": "Numbers computed by deterministic engine — not LLM.",
    }
    rprint(json.dumps(payload, indent=2))


if __name__ == "__main__":
    app()

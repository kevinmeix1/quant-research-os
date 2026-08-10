# Phase 1 — Quant Foundation (completed increment)

## Delivered

1. Package `quant_research_os` with CLI entrypoint `quant`
2. Core domain models: ResearchRequest/Plan, Experiment, Strategy, Alpha, BacktestResult, ValidationResult, ReviewResult
3. Metrics surface (`engine/metrics.py`) — prefers sibling `portfolio.eval.metrics` when installed
4. Transaction cost model with optimistic / baseline / pessimistic presets
5. Cross-sectional backtest v0 with **mandatory execution_lag >= 1** and weight drift
6. Data quality report skeleton
7. Synthetic FX markets: momentum, mean-reversion, random, leaky feature helper
8. Strategy protocol (`StrategyBase`)
9. Tests for domain, costs, lag, quality, synthetic discovery sanity

## Not in this increment

- Experiment registry persistence (Phase 2)
- Alpha library (Phase 3)
- LangGraph research agents (Phase 4+)
- DuckDB/parquet lake
- Walk-forward multi-window store
- UI

## How to verify

```bash
pip install -e ".[dev]"
pytest
quant research demo-cs
```

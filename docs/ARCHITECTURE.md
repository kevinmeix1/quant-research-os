# Architecture

See [PRODUCTION_AUDIT.md](PRODUCTION_AUDIT.md) for the full production-readiness audit.

## Principle

```
Deterministic planner / optional future LLM = orchestrator
Deterministic quantitative engine = source of truth
```

Current planner is a **deterministic template** (`agents/core.py`), not an LLM call.
UI/docs must not claim otherwise.

## Layers

1. CLI / Web / FastAPI
2. `ResearchOrchestrator` explicit state machine
3. Allowlisted `ToolRouter`
4. Engines (CS backtest, WF, stats, portfolio, risk)
5. SQLite metadata + artifacts path

## Critical correctness contracts

- `execution_lag >= 1`
- Holdings NAV-renormalized after drift
- Turnover in weight space
- Metrics pinned local (`ddof=0`, full-sample Sortino downside)
- Regime labels shifted by 1 bar
- Alpha metrics require `metrics_source_ids`

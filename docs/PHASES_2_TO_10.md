# Phases 2–10 — Implementation Notes

Delivered in the full-stack build after Phase 1.

## Phase 2 — Experiment registry
- `experiments/registry.py`, `experiments/hashing.py`
- SQLite persistence, configuration hashes, lineage edges

## Phase 3 — Alpha library
- `alpha/registry.py` with provenance enforcement
- Diversification / correlation diagnostics vs existing books
- Momentum baseline seeding for the flagship workflow

## Phase 4 — Agent framework + tools
- `tools/router.py` allowlisted READ/WRITE/EXECUTION tools
- Deterministic agents in `agents/core.py` + prompt library
- Explicit orchestrator graph in `orchestration/runner.py`

## Phase 5 — Validation
- Walk-forward (`engine/walk_forward.py`) with per-window metrics
- Bootstrap / multiple-testing notes (`engine/statistics.py`)
- Parameter surfaces (`engine/robustness.py`)
- Regime analysis (`engine/regime.py`)
- Adversarial Quant checklist

## Phase 6 — Portfolio intelligence
- Risk parity / vol scaling / mean-variance (`engine/portfolio.py`)
- Stress scenarios + Risk Agent veto in orchestrator

## Phase 7 — Autonomous research
- Budget tracker, research memory, knowledge-graph lineage helpers
- End-to-end `ResearchOrchestrator.run(...)`

## Phase 8 — Documents
- Ingest + keyword event extraction with `information_time`
- Explicitly not assumed predictive until backtested

## Phase 9 — Paper trading
- Simulated paper loop + degradation alerts

## Phase 10 — UI / API / CLI
- FastAPI routes per master spec
- `web/index.html` research dashboard
- `quant` CLI: research/experiment/alpha/backtest/portfolio/report/serve

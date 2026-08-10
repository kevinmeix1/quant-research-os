# Quant Research OS

Autonomous AI quantitative research laboratory.

**Hard rule:** LLMs plan, critique, and orchestrate. Deterministic quantitative engines are the sole source of truth for financial metrics.

This package lives beside the sibling `portfolio-agent` engine (`../`) and reuses its proven portfolio math via adapters rather than duplicating it.

## Status

- **Phase 0** — Architecture assessment complete (`docs/PHASE0_ARCHITECTURE.md`)
- **Phase 1** — Quant foundation (in progress)

## Quick start

```bash
cd "/Users/kaiwenmei/Desktop/x11/trading operating system"
python3.11 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
pytest
```

## Layout

```
src/quant_research_os/
  domain/       typed research objects
  engine/       backtest, costs, metrics adapters
  data/         catalog + quality
  features/     feature contracts
  strategies/   strategy protocol + CS engine
  experiments/  experiment registry (Phase 2)
  alpha/        alpha library (Phase 3)
  agents/       research agents (Phase 4+)
  tools/        allowlisted agent tools
  orchestration/
  reporting/
docs/
tests/
```

## Flagship workflow (target)

> Find a robust cross-sectional FX strategy with low correlation to existing momentum strategies.

See `docs/PHASE0_ARCHITECTURE.md` for the full map from sibling components → this OS.

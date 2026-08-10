# Quant Research OS — Phase 0 Architecture Assessment

**Date:** 2026-08-10  
**Status:** Phase 0 complete → Phase 1 in progress  
**Sibling engine:** `/Users/kaiwenmei/Desktop/x11` (`portfolio-agent`)

---

## 1. Executive verdict

The sibling `x11` repository is a **hybrid LLM-research → Black-Litterman portfolio system** with a correct hard boundary:

> LLM = research / views · Deterministic code = weights / risk / orders

That principle aligns with Quant Research OS. However, `x11` is optimized for **equity portfolio rebalancing and paper execution**, not for **autonomous cross-sectional alpha research** (FX, feature libraries, experiment lineage, adversarial quant review loops).

**Decision:** Build Quant Research OS in this folder as a new product layer that **reuses** the sibling deterministic engine via adapters. Do **not** rewrite BL / optimizer / risk / OMS / audit. Do **not** let agents invent Sharpe or other metrics.

```
LLM agents (this package)
        ↓ tool calls
Quant Tool Layer (this package)
        ↓ adapters
Deterministic Quant Engine (sibling portfolio-agent + new CS engine)
        ↓
Research DB / Alpha Library / Reports (this package)
```

---

## 2. Sibling repository inventory

### 2.1 What exists and is strong

| Area | Location | Assessment |
|---|---|---|
| Design principle (LLM ≠ numbers) | `docs/DESIGN.md` | Aligns with QROS §0 — reuse |
| View contract → BL | `views/`, `quant/black_litterman.py` | Reuse for portfolio construction |
| Covariance / optimizer | `quant/covariance.py`, `optimizer.py` | Reuse |
| IPS + risk limits + kill switch | `ips/`, `risk/` | Reuse for Risk Agent veto |
| Rebalance planner | `quant/rebalance.py`, `planner.py` | Reuse |
| LangGraph pipeline + HITL | `orchestration/` | Pattern reuse; new research graph needed |
| Agentic mode (no execution) | `agentic/` + `guard.py` | Pattern reuse for tool safety |
| Adversarial critic (thesis) | `agents/critic.py`, `challenger.py` | Seed for Adversarial Quant Agent |
| Audit / lineage | `audit/` | Adapt into research traces |
| Param promotion | `promotion/` | Adapt into experiment/alpha lifecycle |
| Paper OMS (Alpaca) | `exec/` | Reuse for Phase 9 paper trading |
| Metrics helpers | `eval/metrics.py` | Reuse Sharpe/Sortino/MDD/IC |
| Monthly walk-forward sketch | `eval/backtest.py` | Reuse structure; fix simulation |
| FastAPI + Next.js console | `api/`, `web/` | Later adapt for research dashboard |
| CLI (Typer) | `cli/` | Pattern for `quant` CLI |

### 2.2 What exists but is thin / incorrect for QROS

| Area | Gap | Severity |
|---|---|---|
| Backtest simulation | Same-day weight application on `pct_change`; no weight drift between rebalances; flat `cost_bps` only | **High** — optimistic PnL |
| Param promotion metrics | `promotion/evaluate.py` passes equity curve into `compute_performance_metrics` (expects returns) | **High** — broken gates |
| Market data | yfinance + SQLite cache only; no parquet/DuckDB; no FX universe | **High** for flagship FX workflow |
| Feature / alpha library | Only `momentum_views` proxy + LLM views | **High** |
| Cross-sectional engine | IC/decile helpers only; no rank/basket construction | **High** |
| Walk-forward | Monthly only; no expanding/rolling windows stored per period; no purged/embargo | Medium |
| Statistical validation | No bootstrap / deflated Sharpe / PBO | Medium |
| Regime analysis | Heuristic technical context only | Medium |
| Diversification analysis | Absent | Medium |
| Experiment registry | Param versions ≠ research experiments | Medium |
| LLM knowledge cutoff | Config present; not enforced in forecast eval | Medium |
| Data quality system | Absent | Medium |
| Synthetic / leakage harness | Weak (RNG tests + Profit Mirage heuristics) | Medium |

### 2.3 What is missing entirely (must build)

1. Research domain objects (`ResearchRequest`, `ResearchPlan`, `Experiment`, `Alpha`, …)
2. Research orchestrator graph (planner → data → hypothesis → experiment → validation → adversarial → report)
3. Data discovery + deterministic data-quality reports
4. Feature framework with information/availability timestamps
5. Cross-sectional strategy engine (FX flagship)
6. Alpha registry + lifecycle states
7. Experiment DB with reproducibility hashes
8. Diversification / factor / regime / robustness agents (deterministic cores + LLM interpretation)
9. Research memory + knowledge graph
10. Document/event branch (Phase 8)
11. `quant` CLI + research API surface
12. Synthetic markets (momentum / mean-reversion / random / leakage)

---

## 3. Component → QROS layer mapping

```
QROS Layer                         Sibling module                         Action
─────────────────────────────────  ─────────────────────────────────────  ────────
User / UI                          web/, api/                             Later adapt
Research Orchestrator              orchestration/ pattern                 NEW graph
Research / Data / Strategy Agents  agents/, agentic/, frameworks/         NEW + adapt
Quant Tool Layer                   agentic/tools.py pattern               NEW allowlist
Deterministic Quant Engine         quant/*, eval/metrics.py               ADAPTER
Data Store                         data/market.py, data/cache.py          ADAPTER → lake
Backtests                          eval/backtest.py                       FIX + extend
Portfolio Engine                   quant/optimizer, rebalance, BL         REUSE
Risk Engine                        risk/*                                 REUSE
Research Database                  promotion/, audit/, beliefs/           NEW schema
Alpha Knowledge Base               (none)                                 BUILD
Reports / UI                       eval/report.py, web/                   EXTEND
```

---

## 4. Quantitative correctness risks (must address in Phase 1+)

### 4.1 Look-ahead / timing

- **Same-bar execution:** `_simulate_returns` applies new weights and earns that day's return. QROS default must be **signal at close t → execute at open/close t+1**.
- **No weight drift:** Holding constant target weights between rebalances overstates performance vs mark-to-market of fixed shares.
- **Price-as-cap prior** in BL walk-forward distorts equilibrium returns.

### 4.2 Data leakage

- yfinance adjusted prices are convenient but not a research-grade PIT store.
- LLM views dated `as_of=today` while scoring historical windows invite narrative leakage.
- No feature `availability_timestamp` contract yet.

### 4.3 LLM fabricating metrics

Sibling design already forbids LLM weights/orders. QROS hardens this:

- Tools return typed metric objects.
- Agents may only cite tool-result IDs.
- Report generator refuses free-text numeric claims without provenance.

### 4.4 Overfitting / multiple testing

No experiment budget or hypothesis counter in sibling. QROS will track `hypotheses_generated`, `experiments_run`, `candidates_rejected` from day one of the registry.

---

## 5. Target architecture (this package)

```
trading operating system/
├── docs/                          # architecture, ADRs, phase notes
├── configs/                       # research budgets, cost models, universes
├── src/quant_research_os/
│   ├── domain/                    # pydantic domain objects
│   ├── data/                      # catalog, quality, adapters to sibling/parquet
│   ├── features/                  # feature specs + deterministic generators
│   ├── strategies/                # Strategy protocol + CS engine
│   ├── engine/                    # backtest, costs, walk-forward, metrics adapters
│   ├── alpha/                     # AlphaRegistry + lifecycle
│   ├── experiments/               # Experiment store + reproducibility
│   ├── portfolio/                 # diversification, allocation adapters
│   ├── risk/                      # stress + veto adapters
│   ├── agents/                    # prompts + structured outputs
│   ├── orchestration/             # LangGraph research state machine
│   ├── tools/                     # allowlisted READ / WRITE / EXECUTION tools
│   ├── memory/                    # structured DB + optional vector notes
│   ├── reporting/                 # honest research reports
│   ├── paper/                     # paper trading (later)
│   ├── api/                       # FastAPI
│   └── cli/                       # `quant` Typer app
├── tests/
│   ├── unit/
│   ├── integration/
│   └── synthetic/                 # known-alpha / random / leakage markets
└── data/                          # local parquet + duckdb + research metadata
```

### Architectural principles (locked)

1. **Sibling engine is source of truth** for portfolio math already proven there.
2. **New CS backtester** lives here; sibling monthly WF is wrapped, then replaced for research paths.
3. **LLM never computes** Sharpe, corr, IC, drawdown, costs, exposures.
4. **Explicit research graph** — no unbounded `while ask_llm`.
5. **Research budgets** on every request.
6. **Rejection is a first-class outcome.**
7. **No live trading tools** in v1 (paper only).

---

## 6. Agent graph (target)

```
START
  → ResearchPlanner
  → DataDiscovery
  → HypothesisGeneration
  → ExperimentDesign
  → ExperimentExecution          # deterministic tools only
  → StatisticalValidation
  → RobustnessTesting
  → RegimeAnalysis
  → DiversificationAnalysis
  → AdversarialReview
  → RobustGate?
       NO  → MoreResearch (budget permitting) → ExperimentDesign
       YES → PortfolioAnalysis → RiskReview → PaperTrading? → Report
  → END
```

Every transition records: `reason`, `budget_remaining`, `tool_result_ids`.

---

## 7. Database schema (Phase 0 design)

### Metadata (SQLite initially; Postgres later if needed)

| Table | Purpose |
|---|---|
| `research_requests` | User questions + status |
| `research_plans` | Structured plans |
| `hypotheses` | Competing economic hypotheses |
| `experiments` | Config hash, seeds, periods, status |
| `strategies` | Versioned strategy definitions |
| `alphas` | Lifecycle + links to strategy/hypothesis |
| `backtest_results` | Metrics JSON + artifact paths |
| `validation_results` | IS/OOS/WF/robustness |
| `reviews` | Adversarial findings |
| `agent_traces` | Observability |
| `reports` | Final report blobs + decision |

### Analytical store

- **Parquet** for OHLCV / features / equity curves / positions
- **DuckDB** for analytical queries over parquet
- Do **not** store millions of bars in ORM tables

### Vector store (optional, later)

- Research report text, qualitative notes only
- Never authoritative for metrics

---

## 8. API / CLI design (Phase 0)

### CLI (`quant`)

```
quant research "..."
quant research list | inspect <id> | trace <id>
quant experiment list | inspect <id>
quant backtest <strategy>
quant alpha list | inspect <id>
quant portfolio
quant report <research_id>
```

### API (FastAPI)

```
POST/GET /research …
GET /research/{id}/trace
POST /research/{id}/cancel
GET/POST /experiments …
GET /strategies …
GET /alphas …
GET /backtests/{id}
GET /reports/{id}
GET /portfolio …
```

---

## 9. Testing strategy

| Tier | Focus |
|---|---|
| Unit | Domain models, cost models, feature timestamps, CS ranking, metrics |
| Property | No future data in features; execution lag ≥ 1 bar |
| Synthetic markets | Discover known momentum/MR; fail on random; flag leaked feature |
| Adapter | Sibling metrics/optimizer produce identical results through adapters |
| Agent eval (later) | Decision quality benchmarks, not just “graph runs” |

---

## 10. Phase plan (confirmed)

| Phase | Deliverable | Status |
|---|---|---|
| **0** | This assessment + package scaffold | **Done** |
| **1** | Quant foundation: domain models, metrics adapter, cost model, lagged CS backtest stub, data quality skeleton | **Next** |
| **2** | Experiment registry + reproducibility hashes | Pending |
| **3** | Alpha library + correlation analysis | Pending |
| **4** | Agent framework (planner/data/hypothesis/experiment) | Pending |
| **5** | Validation agents (stat/robustness/regime/div/adversarial) | Pending |
| **6** | Portfolio intelligence | Pending |
| **7** | Autonomous research loops + budgets | Pending |
| **8** | Financial documents / events | Pending |
| **9** | Paper trading + monitoring | Pending |
| **10** | Research OS UI | Pending |

---

## 11. Phase 1 — smallest useful increment

1. Package scaffold (`quant_research_os`) with path dependency on sibling `portfolio-agent`.
2. Core pydantic domain models from the master spec.
3. Metrics adapter wrapping sibling `compute_performance_metrics` (no metric duplication).
4. Transaction cost model (proportional / fixed / spread / optimistic|baseline|pessimistic).
5. Cross-sectional backtest engine v0 with **mandatory 1-bar execution lag** and weight drift.
6. Data quality report skeleton + synthetic FX panel generator for tests.
7. Tests proving: lag prevents same-bar lookahead; metrics come from adapter; costs reduce Sharpe.

---

## 12. Explicit non-goals for Phase 1

- No LangGraph research loop yet
- No LLM calls
- No UI
- No live broker tools
- No document ingestion
- No DuckDB lake migration yet (interfaces only)

---

## 13. Dependency decisions

| Choice | Decision | Why |
|---|---|---|
| Workflow engine | LangGraph (when agents land) | Already in sibling; explicit graphs |
| Domain models | Pydantic v2 | Matches sibling |
| Analytical DB | DuckDB + parquet (Phase 1+ interfaces) | Spec §50 |
| Metadata DB | SQLite first | Simple, local, reproducible |
| Sibling integration | Path dependency / editable install | Avoid rewriting quant math |
| Package name | `quant_research_os` | Import-safe; product name remains Quant Research OS |
| Folder name | `trading operating system` | Per user request |

---

## 14. Success criteria for Phase 0 exit

- [x] Sibling assessed
- [x] Reuse / adapt / build map written
- [x] Correctness risks documented
- [x] Phase plan locked
- [x] Phase 1 increment defined
- [ ] Scaffold + Phase 1 increment implemented with tests

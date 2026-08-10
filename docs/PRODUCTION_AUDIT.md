# Quant Research OS — Production Readiness Audit

**Date:** 2026-08-10  
**Scope:** Full repository inspection (no rewrite)  
**Overall score:** **3.2 / 10** — capable local research prototype; not production-ready

Interactive summary: open the Production Readiness Audit canvas beside chat.

---

## Executive verdict

| Strength | Weakness |
|---|---|
| Metric provenance rule on AlphaRegistry | PnL/weight-drift accounting incorrect |
| Explicit research state machine | No resume / cancel / crash recovery |
| Allowlisted tools (no shell) | Unauthenticated blocking API |
| Synthetic markets + e2e path | Paper trading is IID noise |
| Domain models + experiment hashes | Blob SQLite, no FKs/WAL/indexes |

**Principle status:** Partially upheld. Numbers come from tools, but UI/docs overclaim LLM agency, and paper path invents returns without the engine.

---

## CRITICAL findings

### C1 — Weight drift PnL without NAV renormalization
- **Problem:** `holdings *= (1+r)` without dividing by `(1+port_ret)`.
- **Impact:** Compounded returns/Sharpe/drawdown wrong between rebalances.
- **Severity:** CRITICAL
- **Solution:** NAV-normalize after mark-to-market.
- **Complexity:** M

### C2 — Turnover vs drifted notional
- **Problem:** `|target_unit_w - drifted_notional|` used as turnover.
- **Impact:** Costs wrong; net performance corrupted.
- **Severity:** CRITICAL
- **Solution:** Convert holdings to current weights before turnover.
- **Complexity:** M

### C3 — Unauthenticated sync `POST /research`
- **Problem:** No auth; full research on request thread; CORS `*`.
- **Impact:** DoS / state mutation if exposed.
- **Severity:** CRITICAL
- **Solution:** API key, async jobs, localhost-only default.
- **Complexity:** M

### C4 — Global `_db` + `_CACHE`
- **Problem:** Import-time singletons.
- **Impact:** Cross-run pollution; no isolation.
- **Severity:** CRITICAL
- **Solution:** FastAPI `Depends`; scoped cache.
- **Complexity:** M

### C5 — No resume; crash leaves `RUNNING`
- **Problem:** Linear `run()`; no checkpoints; cancel is cosmetic.
- **Impact:** Restart from zero; orphan rows.
- **Severity:** CRITICAL
- **Solution:** Persist checkpoints; `FAILED` on exception; cancel flag.
- **Complexity:** L (full resume) / S–M (FAILED + cancel + checkpoint stub)

---

## HIGH findings

| ID | Problem |
|---|---|
| H1 | Rolling WF always slices `[:ve]` — ignores `train_start` |
| H2 | Overlapping WF windows double-count OOS |
| H3 | Sibling vs local metrics (ddof mismatch) |
| H4 | Regime labels include same-day return |
| H5 | `PAPER_TRADING` excluded from report survivors |
| H6 | Paper trading = `N(μ,σ)` noise |
| H7 | LLM prompts unused; planner is fixed template |
| H8 | Blob SQLite; no FKs/indexes/WAL; dynamic SQL |
| H9 | Cancel does not stop work |
| H10 | Close-only “open fill” earns overnight gap |

---

## MEDIUM / LOW (selected)

- Sortino uses std of negative days only (inflated)
- Quality checks not gated into backtest
- Seed momentum alpha every run (library pollution)
- Empty library → vacuous `genuine_diversification=True`
- Tool traces log full return vectors
- Dashboard XSS via `innerHTML`
- No Docker/CI/migrations
- Config YAML never loaded
- Anti-lookahead test does not assert the property

---

## Category scores

| Category | Score | Remaining risks | Next step |
|---|---|---|---|
| Quantitative correctness | 4/10 | PnL, WF, fills | Fix C1–C2, H1–H3 |
| Agent reliability | 3/10 | No real LLM loop | Honest docs or wire LLM |
| Data reliability | 4/10 | Synthetic-only | Quality gate + lake |
| API reliability | 3/10 | Sync/cancel | Jobs + auth |
| Security | 2/10 | Open API | Keys + XSS + SQL allowlist |
| Observability | 3/10 | Thin traces | structlog + IDs |
| Performance | 5/10 | JSON returns | Parquet artifacts |
| Scalability | 2/10 | Global state | Workers + WAL |
| Testing | 5/10 | Weak invariants | Adversarial suite |
| Deployment | 1/10 | None | Docker + CI |

---

## Remediation order (Phase 14)

1. Fix C1–C2 (quant truth)
2. Pin metrics (H3); Sortino; WF H1–H2; regime H4
3. Report H5; seed idempotency; FAILED/cancel
4. Storage WAL + SQL allowlist
5. API DI + API key + job wrapper
6. Adversarial tests + docs honesty
7. Defer: full resume, real paper replay, real LLM (document as known gaps)

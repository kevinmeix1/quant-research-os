# AGENTS

## Current mode: deterministic research pipeline

| Role | Implementation |
|---|---|
| Planner | `plan_research()` fixed hypothesis set |
| Data | tools: list/inspect/validate datasets |
| Adversarial | checklist over tool outputs |
| Orchestrator | explicit state machine + budgets |

`agents/prompts.py` is reserved for a future LLM mode. Do not claim LLM planning until wired.

## Hard rules

- Structured outputs (`AgentDecision`, `ReviewResult`, reports)
- Numbers only via tools
- Research budgets (`max_experiments`)
- Cooperative cancel between hypotheses
- Fail → `FAILED` status + trace

## Known gaps

- No LLM retries/timeouts/circuit breakers (no LLM calls)
- Checkpoint saved but full resume-from-node not implemented
- Paper trading is IID noise simulation (labeled)

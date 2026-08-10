"""Research budget tracking — prevents infinite loops."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class BudgetTracker:
    max_experiments: int = 50
    max_llm_calls: int = 200
    max_runtime_seconds: int = 3600
    experiments_used: int = 0
    llm_calls_used: int = 0
    hypotheses_generated: int = 0
    candidates_rejected: int = 0
    candidates_promising: int = 0
    candidates_robust: int = 0

    def can_run_experiment(self) -> bool:
        return self.experiments_used < self.max_experiments

    def consume_experiment(self) -> None:
        if not self.can_run_experiment():
            raise RuntimeError("experiment budget exhausted")
        self.experiments_used += 1

    def consume_llm(self) -> None:
        self.llm_calls_used += 1
        if self.llm_calls_used > self.max_llm_calls:
            raise RuntimeError("LLM budget exhausted")

    def snapshot(self) -> dict:
        return {
            "max_experiments": self.max_experiments,
            "experiments_used": self.experiments_used,
            "max_llm_calls": self.max_llm_calls,
            "llm_calls_used": self.llm_calls_used,
            "hypotheses_generated": self.hypotheses_generated,
            "candidates_rejected": self.candidates_rejected,
            "candidates_promising": self.candidates_promising,
            "candidates_robust": self.candidates_robust,
            "remaining_experiments": self.max_experiments - self.experiments_used,
        }

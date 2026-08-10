"""Honest research report generator — metrics must cite tool provenance."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from pydantic import BaseModel, Field

from quant_research_os.domain.enums import ResearchDecision


class ResearchReport(BaseModel):
    research_id: str
    question: str
    executive_summary: str
    decision: ResearchDecision
    hypotheses_tested: int = 0
    experiments_run: int = 0
    candidates_rejected: int = 0
    candidates_surviving: int = 0
    best_candidate: dict[str, Any] | None = None
    sections: dict[str, Any] = Field(default_factory=dict)
    limitations: list[str] = Field(default_factory=list)
    reproducibility: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    def to_markdown(self) -> str:
        lines = [
            f"# Research Report — {self.research_id}",
            "",
            f"**Decision:** {self.decision.value}",
            "",
            "## Research Question",
            self.question,
            "",
            "## Executive Summary",
            self.executive_summary,
            "",
            "## Multiple-Testing Disclosure",
            f"- Hypotheses tested: {self.hypotheses_tested}",
            f"- Experiments run: {self.experiments_run}",
            f"- Candidates rejected: {self.candidates_rejected}",
            f"- Candidates surviving: {self.candidates_surviving}",
            "",
        ]
        if self.best_candidate:
            lines += ["## Best Candidate", "```json", str(self.best_candidate), "```", ""]
        for title, body in self.sections.items():
            lines += [f"## {title}", ""]
            if isinstance(body, str):
                lines.append(body)
            else:
                lines.append(f"```json\n{body}\n```")
            lines.append("")
        lines += ["## Limitations", ""]
        for lim in self.limitations:
            lines.append(f"- {lim}")
        lines += ["", "## Reproducibility", f"```json\n{self.reproducibility}\n```", ""]
        lines += [
            "",
            "## Interpretation Guardrails",
            "- Metrics above are from deterministic tools, not LLM estimates.",
            "- Correlation is not causation; backtest ≠ live performance.",
            "- Out-of-sample evidence outweighs in-sample beauty.",
            "",
        ]
        return "\n".join(lines)


def build_report(
    *,
    research_id: str,
    question: str,
    decision: ResearchDecision,
    budget_snapshot: dict[str, Any],
    plan: dict[str, Any],
    data_section: dict[str, Any],
    candidates: list[dict[str, Any]],
    reviews: list[dict[str, Any]],
    portfolio: dict[str, Any] | None,
    risk: dict[str, Any] | None,
    reproducibility: dict[str, Any],
) -> ResearchReport:
    surviving = [c for c in candidates if c.get("status") in {"PROMISING", "ROBUST"}]
    rejected = [c for c in candidates if c.get("status") == "REJECTED"]
    best = None
    if surviving:
        best = max(surviving, key=lambda c: (c.get("metrics") or {}).get("sharpe", float("-inf")))

    if decision == ResearchDecision.NO_ROBUST_ALPHA_FOUND:
        summary = (
            "No candidate survived robustness, diversification, and adversarial gates "
            "under the stated assumptions. A failed research project is a valid result."
        )
    elif best:
        m = best.get("metrics") or {}
        summary = (
            f"Best surviving candidate '{best.get('name')}' shows tool-computed "
            f"Sharpe={m.get('sharpe')}, max_drawdown={m.get('max_drawdown')}. "
            f"Evidence is provisional; see OOS/walk-forward and adversarial sections."
        )
    else:
        summary = "Research completed without a clear surviving candidate."

    limitations = [
        "Synthetic or limited datasets may not represent live FX microstructure.",
        "Carry/value/liquidity features may be proxies when true fundamentals are unavailable.",
        "Statistical significance weakens under multiple testing — see trial counts.",
        "Transaction-cost models are assumptions, not guarantees of executable fills.",
        "Regime labels are heuristic, not ground truth.",
    ]

    return ResearchReport(
        research_id=research_id,
        question=question,
        executive_summary=summary,
        decision=decision,
        hypotheses_tested=budget_snapshot.get("hypotheses_generated", 0),
        experiments_run=budget_snapshot.get("experiments_used", 0),
        candidates_rejected=len(rejected),
        candidates_surviving=len(surviving),
        best_candidate=best,
        sections={
            "Economic Motivation": plan.get("economic_hypothesis", ""),
            "Existing Alpha Portfolio": data_section.get("existing_library", {}),
            "Candidate Hypotheses": plan.get("candidate_hypotheses", []),
            "Data": data_section.get("datasets", {}),
            "Experimental Results": candidates,
            "Adversarial Review": reviews,
            "Portfolio Impact": portfolio or {},
            "Risk Review": risk or {},
            "Budget": budget_snapshot,
        },
        limitations=limitations,
        reproducibility=reproducibility,
    )

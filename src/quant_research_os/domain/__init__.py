"""Strongly typed research domain objects.

Financial metrics fields on these models must be populated only from
deterministic engine / tool results — never from LLM free text.
"""

from quant_research_os.domain.alpha import Alpha, AlphaStatus
from quant_research_os.domain.backtest import BacktestResult
from quant_research_os.domain.enums import ResearchDecision, ResearchStatus, Severity
from quant_research_os.domain.experiment import Experiment, ExperimentStatus
from quant_research_os.domain.research import ResearchPlan, ResearchRequest
from quant_research_os.domain.review import ReviewResult
from quant_research_os.domain.strategy import Strategy
from quant_research_os.domain.validation import ValidationResult

__all__ = [
    "Alpha",
    "AlphaStatus",
    "BacktestResult",
    "Experiment",
    "ExperimentStatus",
    "ResearchDecision",
    "ResearchPlan",
    "ResearchRequest",
    "ResearchStatus",
    "ReviewResult",
    "Severity",
    "Strategy",
    "ValidationResult",
]

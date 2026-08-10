"""Strategy protocol — human-written and agent-generated strategies share this contract."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

import pandas as pd

from quant_research_os.domain.strategy import Strategy


class StrategyBase(ABC):
    @abstractmethod
    def metadata(self) -> Strategy:
        raise NotImplementedError

    @abstractmethod
    def required_data(self) -> list[str]:
        raise NotImplementedError

    @abstractmethod
    def generate_features(self, data: dict[str, pd.DataFrame]) -> pd.DataFrame:
        raise NotImplementedError

    @abstractmethod
    def generate_signal(self, features: pd.DataFrame) -> pd.DataFrame:
        raise NotImplementedError

    @abstractmethod
    def generate_positions(self, signal: pd.DataFrame) -> pd.DataFrame:
        raise NotImplementedError

    def position_limits(self) -> dict[str, Any]:
        return {"max_gross": 1.0, "max_net": 0.25}

    def rebalance_schedule(self) -> str:
        return "every_n_bars"

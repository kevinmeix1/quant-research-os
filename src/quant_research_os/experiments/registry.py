"""Experiment registry with lineage and reproducibility metadata."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from quant_research_os.domain.backtest import BacktestResult
from quant_research_os.domain.enums import ExperimentStatus
from quant_research_os.domain.experiment import Experiment
from quant_research_os.domain.validation import ValidationResult
from quant_research_os.experiments.hashing import code_commit, configuration_hash
from quant_research_os.storage.db import ResearchDB


class ExperimentRegistry:
    def __init__(self, db: ResearchDB | None = None) -> None:
        self.db = db or ResearchDB()

    def create(self, experiment: Experiment) -> Experiment:
        cfg = {
            "parameters": experiment.parameters,
            "strategy_id": experiment.strategy_id,
            "dataset_id": experiment.dataset_id,
            "training_period": experiment.training_period,
            "validation_period": experiment.validation_period,
            "test_period": experiment.test_period,
            "transaction_cost_model": experiment.transaction_cost_model,
            "slippage_model": experiment.slippage_model,
            "random_seed": experiment.random_seed,
        }
        experiment.configuration_hash = configuration_hash(cfg)
        experiment.code_version = experiment.code_version or code_commit()
        experiment.status = ExperimentStatus.PENDING
        self.db.upsert_json(
            "experiments",
            "experiment_id",
            experiment.experiment_id,
            experiment.model_dump(mode="json"),
            research_id=experiment.research_id,
            status=experiment.status.value,
            configuration_hash=experiment.configuration_hash,
            created_at=experiment.created_at.isoformat(),
        )
        if experiment.hypothesis_id:
            self.db.add_edge("hypothesis", experiment.hypothesis_id, "tested_by", "experiment", experiment.experiment_id)
        if experiment.strategy_id:
            self.db.add_edge("strategy", experiment.strategy_id, "used_in", "experiment", experiment.experiment_id)
        if experiment.research_id:
            self.db.add_edge("research", experiment.research_id, "has_experiment", "experiment", experiment.experiment_id)
        return experiment

    def save(self, experiment: Experiment) -> None:
        self.db.upsert_json(
            "experiments",
            "experiment_id",
            experiment.experiment_id,
            experiment.model_dump(mode="json"),
            research_id=experiment.research_id,
            status=experiment.status.value,
            configuration_hash=experiment.configuration_hash,
            created_at=experiment.created_at.isoformat(),
        )

    def get(self, experiment_id: str) -> Experiment | None:
        raw = self.db.get_json("experiments", "experiment_id", experiment_id)
        return Experiment.model_validate(raw) if raw else None

    def list(self, research_id: str | None = None) -> list[Experiment]:
        if research_id:
            rows = self.db.list_json("experiments", "research_id=?", (research_id,))
        else:
            rows = self.db.list_json("experiments")
        return [Experiment.model_validate(r) for r in rows]

    def complete(self, experiment_id: str, *, error: str | None = None) -> Experiment:
        exp = self.get(experiment_id)
        if not exp:
            raise KeyError(experiment_id)
        exp.status = ExperimentStatus.FAILED if error else ExperimentStatus.COMPLETED
        exp.error = error
        exp.completed_at = datetime.now(timezone.utc)
        self.save(exp)
        return exp

    def save_backtest(self, result: BacktestResult) -> None:
        self.db.upsert_json(
            "backtest_results",
            "backtest_id",
            result.backtest_id,
            result.model_dump(mode="json"),
        )
        if result.experiment_id:
            self.db.add_edge("experiment", result.experiment_id, "produced", "backtest", result.backtest_id)

    def get_backtest(self, backtest_id: str) -> BacktestResult | None:
        raw = self.db.get_json("backtest_results", "backtest_id", backtest_id)
        return BacktestResult.model_validate(raw) if raw else None

    def save_validation(self, result: ValidationResult) -> None:
        self.db.upsert_json(
            "validation_results",
            "validation_id",
            result.validation_id,
            result.model_dump(mode="json"),
            experiment_id=result.experiment_id,
        )
        self.db.add_edge("experiment", result.experiment_id, "validated_by", "validation", result.validation_id)

    def counts(self, research_id: str) -> dict[str, int]:
        exps = self.list(research_id)
        return {
            "experiments_total": len(exps),
            "experiments_completed": sum(1 for e in exps if e.status == ExperimentStatus.COMPLETED),
            "experiments_failed": sum(1 for e in exps if e.status == ExperimentStatus.FAILED),
        }

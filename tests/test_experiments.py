from __future__ import annotations

from quant_research_os.domain.experiment import Experiment
from quant_research_os.experiments.hashing import configuration_hash
from quant_research_os.experiments.registry import ExperimentRegistry


def test_experiment_registry_hash_and_lineage(tmp_db):
    reg = ExperimentRegistry(tmp_db)
    exp = Experiment(
        research_id="RES-test",
        parameters={"lookback": 20, "signal": "momentum"},
        dataset_id="fx_synthetic_momentum",
        random_seed=1,
    )
    saved = reg.create(exp)
    assert saved.configuration_hash
    assert len(saved.configuration_hash) == 16
    # Same config → same hash
    h2 = configuration_hash(
        {
            "parameters": {"lookback": 20, "signal": "momentum"},
            "strategy_id": None,
            "dataset_id": "fx_synthetic_momentum",
            "training_period": None,
            "validation_period": None,
            "test_period": None,
            "transaction_cost_model": "baseline",
            "slippage_model": "baseline",
            "random_seed": 1,
        }
    )
    assert saved.configuration_hash == h2
    got = reg.get(saved.experiment_id)
    assert got is not None
    edges = tmp_db.lineage_for(saved.experiment_id)
    assert any(e["rel"] == "has_experiment" or e["dst_id"] == saved.experiment_id for e in edges)

"""Dataset catalog for data discovery agent."""

from __future__ import annotations

from typing import Any

import pandas as pd
from pydantic import BaseModel, Field

from quant_research_os.data.quality import DataQualityReport, profile_price_panel
from quant_research_os.data.synthetic import (
    synthetic_mean_reversion_fx,
    synthetic_momentum_fx,
    synthetic_random_fx,
)


class DatasetInfo(BaseModel):
    dataset_id: str
    name: str
    universe: str
    frequency: str
    n_instruments: int
    date_start: str | None = None
    date_end: str | None = None
    source: str
    description: str
    columns: list[str] = Field(default_factory=list)


_CACHE: dict[str, pd.DataFrame] = {}


def list_datasets() -> list[DatasetInfo]:
    specs = [
        ("fx_synthetic_momentum", "Synthetic FX momentum market", "FX_G10", "synthetic_momentum"),
        ("fx_synthetic_meanrev", "Synthetic FX mean-reversion market", "FX_G10", "synthetic_meanrev"),
        ("fx_synthetic_random", "Synthetic FX random market", "FX_G10", "synthetic_random"),
    ]
    out = []
    for did, name, uni, _ in specs:
        px = load_dataset(did)
        out.append(
            DatasetInfo(
                dataset_id=did,
                name=name,
                universe=uni,
                frequency="1D",
                n_instruments=px.shape[1],
                date_start=str(px.index.min().date()),
                date_end=str(px.index.max().date()),
                source="synthetic",
                description=name,
                columns=list(px.columns),
            )
        )
    return out


def load_dataset(dataset_id: str) -> pd.DataFrame:
    if dataset_id in _CACHE:
        return _CACHE[dataset_id]
    if dataset_id == "fx_synthetic_momentum":
        px = synthetic_momentum_fx(n_days=756, seed=42, momentum_strength=0.025)
    elif dataset_id == "fx_synthetic_meanrev":
        px = synthetic_mean_reversion_fx(n_days=756, seed=7)
    elif dataset_id == "fx_synthetic_random":
        px = synthetic_random_fx(n_days=756, seed=99)
    else:
        raise KeyError(f"unknown dataset: {dataset_id}")
    _CACHE[dataset_id] = px
    return px


def inspect_dataset(dataset_id: str) -> dict[str, Any]:
    info = next(d for d in list_datasets() if d.dataset_id == dataset_id)
    px = load_dataset(dataset_id)
    return {
        **info.model_dump(),
        "missing_pct": float(px.isna().mean().mean()),
        "head": px.head(3).round(4).to_dict(),
    }


def validate_dataset(dataset_id: str) -> DataQualityReport:
    return profile_price_panel(load_dataset(dataset_id), dataset_id=dataset_id)


def query_market_data(dataset_id: str, start: str | None = None, end: str | None = None) -> pd.DataFrame:
    px = load_dataset(dataset_id)
    if start:
        px = px.loc[start:]
    if end:
        px = px.loc[:end]
    return px

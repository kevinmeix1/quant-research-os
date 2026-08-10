"""Data catalog and quality surfaces."""

from quant_research_os.data.catalog import (
    inspect_dataset,
    list_datasets,
    load_dataset,
    query_market_data,
    validate_dataset,
)
from quant_research_os.data.quality import DataQualityReport, profile_price_panel
from quant_research_os.data.synthetic import (
    synthetic_leaky_feature,
    synthetic_mean_reversion_fx,
    synthetic_momentum_fx,
    synthetic_random_fx,
)

__all__ = [
    "DataQualityReport",
    "inspect_dataset",
    "list_datasets",
    "load_dataset",
    "profile_price_panel",
    "query_market_data",
    "synthetic_leaky_feature",
    "synthetic_mean_reversion_fx",
    "synthetic_momentum_fx",
    "synthetic_random_fx",
    "validate_dataset",
]

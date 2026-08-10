"""Feature library for cross-sectional research."""

from __future__ import annotations

import pandas as pd

from quant_research_os.features.spec import FeatureSpec


def momentum(prices: pd.DataFrame, lookback: int = 20) -> pd.DataFrame:
    return prices / prices.shift(lookback) - 1.0


def reversal(prices: pd.DataFrame, lookback: int = 5) -> pd.DataFrame:
    return -momentum(prices, lookback)


def volatility(prices: pd.DataFrame, lookback: int = 20) -> pd.DataFrame:
    return prices.pct_change().rolling(lookback).std()


def carry_proxy(prices: pd.DataFrame, lookback: int = 60) -> pd.DataFrame:
    """Interest-rate carry proxy: slow drift / level — synthetic stand-in when true carry unavailable."""
    return prices.pct_change().rolling(lookback).mean()


def value_proxy(prices: pd.DataFrame, lookback: int = 120) -> pd.DataFrame:
    """Cheapness vs moving average (contrarian value proxy)."""
    ma = prices.rolling(lookback).mean()
    return ma / prices - 1.0


def liquidity_proxy(prices: pd.DataFrame, lookback: int = 20) -> pd.DataFrame:
    """Inverse volatility as liquidity/stability proxy."""
    vol = volatility(prices, lookback).replace(0, pd.NA)
    return 1.0 / vol


FEATURE_GENERATORS = {
    "momentum": momentum,
    "reversal": reversal,
    "volatility": volatility,
    "carry": carry_proxy,
    "value": value_proxy,
    "liquidity": liquidity_proxy,
}


def feature_specs() -> list[FeatureSpec]:
    return [
        FeatureSpec(
            feature_id="momentum_20d",
            name="momentum",
            formula="close[t]/close[t-20]-1",
            lookback=20,
            required_data=["prices"],
            information_timestamp="close_t",
            availability_timestamp="close_t",
            frequency="1D",
        ),
        FeatureSpec(
            feature_id="reversal_5d",
            name="reversal",
            formula="-(close[t]/close[t-5]-1)",
            lookback=5,
            required_data=["prices"],
            information_timestamp="close_t",
            availability_timestamp="close_t",
            frequency="1D",
        ),
        FeatureSpec(
            feature_id="carry_proxy_60d",
            name="carry",
            formula="rolling_mean(return, 60)",
            lookback=60,
            required_data=["prices"],
            information_timestamp="close_t",
            availability_timestamp="close_t",
            frequency="1D",
            parameters={"note": "proxy when true forward points unavailable"},
        ),
    ]


def compute_feature(name: str, prices: pd.DataFrame, lookback: int | None = None) -> pd.DataFrame:
    if name not in FEATURE_GENERATORS:
        raise KeyError(f"unknown feature: {name}")
    fn = FEATURE_GENERATORS[name]
    if lookback is None:
        return fn(prices)
    return fn(prices, lookback)

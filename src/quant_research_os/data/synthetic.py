"""Synthetic market generators for correctness tests."""

from __future__ import annotations

import numpy as np
import pandas as pd


FX_PAIRS = [
    "EURUSD",
    "GBPUSD",
    "USDJPY",
    "AUDUSD",
    "USDCAD",
    "USDCHF",
    "NZDUSD",
    "EURGBP",
]


def _dates(n: int, start: str = "2018-01-01") -> pd.DatetimeIndex:
    return pd.bdate_range(start=start, periods=n)


def synthetic_momentum_fx(
    n_days: int = 504,
    n_assets: int = 8,
    seed: int = 42,
    momentum_strength: float = 0.04,
) -> pd.DataFrame:
    """Cross-sectional momentum market: recent relative winners keep winning."""
    rng = np.random.default_rng(seed)
    cols = FX_PAIRS[:n_assets]
    # Cross-sectional scores with persistence → momentum works
    score = rng.normal(0, 1, size=n_assets)
    rets = np.zeros((n_days, n_assets))
    for t in range(n_days):
        score = 0.92 * score + rng.normal(0, 0.35, size=n_assets)
        # demean so long-short CS is the edge
        cs = score - score.mean()
        rets[t] = momentum_strength * cs / (np.std(cs) + 1e-8) * 0.01 + rng.normal(0, 0.003, size=n_assets)
    prices = 100 * np.exp(np.cumsum(rets, axis=0))
    return pd.DataFrame(prices, index=_dates(n_days), columns=cols)


def synthetic_mean_reversion_fx(
    n_days: int = 504,
    n_assets: int = 8,
    seed: int = 7,
    strength: float = 0.18,
) -> pd.DataFrame:
    """Short-term cross-sectional reversal: yesterday's relative losers outperform."""
    rng = np.random.default_rng(seed)
    cols = FX_PAIRS[:n_assets]
    rets = np.zeros((n_days, n_assets))
    prev = rng.normal(0, 0.01, size=n_assets)
    for t in range(n_days):
        # Reversal of prior cross-sectional residual
        cs = prev - prev.mean()
        shock = rng.normal(0, 0.004, size=n_assets)
        rets[t] = -strength * cs + shock
        prev = rets[t]
    prices = 100 * np.exp(np.cumsum(rets, axis=0))
    return pd.DataFrame(prices, index=_dates(n_days), columns=cols)


def synthetic_random_fx(
    n_days: int = 504,
    n_assets: int = 8,
    seed: int = 99,
) -> pd.DataFrame:
    """Pure noise — no persistent alpha expected."""
    rng = np.random.default_rng(seed)
    cols = FX_PAIRS[:n_assets]
    rets = rng.normal(0, 0.005, size=(n_days, n_assets))
    prices = 100 * np.exp(np.cumsum(rets, axis=0))
    return pd.DataFrame(prices, index=_dates(n_days), columns=cols)


def synthetic_leaky_feature(prices: pd.DataFrame) -> pd.DataFrame:
    """Deliberately leak future returns into a feature (for leakage tests)."""
    future = prices.pct_change().shift(-1)
    return future.fillna(0.0)

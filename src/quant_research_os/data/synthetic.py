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
    momentum_strength: float = 0.02,
) -> pd.DataFrame:
    """Cross-sectional momentum market: recent winners keep winning (noisy)."""
    rng = np.random.default_rng(seed)
    cols = FX_PAIRS[:n_assets]
    # Latent factor persistence creates CS momentum.
    latent = rng.normal(0, 0.01, size=(n_days, n_assets))
    for t in range(1, n_days):
        latent[t] += 0.85 * latent[t - 1]
    noise = rng.normal(0, 0.005, size=(n_days, n_assets))
    rets = momentum_strength * latent + noise
    prices = 100 * np.exp(np.cumsum(rets, axis=0))
    return pd.DataFrame(prices, index=_dates(n_days), columns=cols)


def synthetic_mean_reversion_fx(
    n_days: int = 504,
    n_assets: int = 8,
    seed: int = 7,
) -> pd.DataFrame:
    """Mean-reverting relative levels → short-term reversal alpha."""
    rng = np.random.default_rng(seed)
    cols = FX_PAIRS[:n_assets]
    x = rng.normal(0, 1, size=(n_days, n_assets))
    for t in range(1, n_days):
        x[t] = 0.7 * x[t - 1] + rng.normal(0, 0.5, size=n_assets)
    # Returns pull back toward cross-sectional mean
    cs_mean = x.mean(axis=1, keepdims=True)
    rets = -0.15 * (x - cs_mean) / 100 + rng.normal(0, 0.004, size=(n_days, n_assets))
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

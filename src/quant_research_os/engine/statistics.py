"""Statistical validation (bootstrap, significance, deflated-Sharpe style checks)."""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd
from pydantic import BaseModel, Field
from scipy import stats


class StatisticalResult(BaseModel):
    n_obs: int
    sharpe: float
    sharpe_ci_low: float
    sharpe_ci_high: float
    mean_return_pvalue: float
    skewness: float
    excess_kurtosis: float
    autocorrelation_lag1: float
    n_trials_tested: int = 1
    deflated_sharpe_approx: float | None = None
    multiple_testing_warning: bool = False
    notes: list[str] = Field(default_factory=list)
    bootstrap_sharpes: list[float] = Field(default_factory=list)


def _ann_sharpe(r: np.ndarray, rf: float = 0.0) -> float:
    if len(r) < 2 or np.std(r, ddof=0) == 0:
        return 0.0
    excess = r - rf / 252.0
    return float(np.mean(excess) / np.std(r, ddof=0) * np.sqrt(252))


def bootstrap_sharpe(
    returns: pd.Series | list[float],
    *,
    n_boot: int = 500,
    block_size: int = 5,
    seed: int = 42,
    risk_free_rate: float = 0.0,
    n_trials_tested: int = 1,
) -> StatisticalResult:
    r = pd.Series(returns, dtype=float).dropna().to_numpy()
    n = len(r)
    notes: list[str] = []
    if n < 30:
        notes.append("Small sample — statistical tests are weak")

    rng = np.random.default_rng(seed)
    boot = []
    # Block bootstrap to respect mild autocorrelation
    if n >= block_size * 2:
        n_blocks = int(np.ceil(n / block_size))
        for _ in range(n_boot):
            starts = rng.integers(0, n - block_size + 1, size=n_blocks)
            sample = np.concatenate([r[s : s + block_size] for s in starts])[:n]
            boot.append(_ann_sharpe(sample, risk_free_rate))
    else:
        for _ in range(n_boot):
            sample = rng.choice(r, size=n, replace=True)
            boot.append(_ann_sharpe(sample, risk_free_rate))

    boot_arr = np.array(boot)
    sharpe = _ann_sharpe(r, risk_free_rate)
    ci_low, ci_high = float(np.quantile(boot_arr, 0.025)), float(np.quantile(boot_arr, 0.975))

    # Simple mean-return t-test vs 0
    tstat, pval = stats.ttest_1samp(r, 0.0) if n > 2 else (0.0, 1.0)
    skew = float(stats.skew(r)) if n > 3 else 0.0
    kurt = float(stats.kurtosis(r)) if n > 3 else 0.0
    ac1 = float(pd.Series(r).autocorr(lag=1) or 0.0) if n > 3 else 0.0

    # Very rough deflated Sharpe adjustment for multiple testing (Bailey & Lopez de Prado inspired)
    # E[max Sharpe] under null ≈ sqrt(2*log(n_trials)) scale heuristic
    multiple = n_trials_tested > 5
    deflated = None
    if multiple:
        notes.append(f"Multiple testing: {n_trials_tested} trials tracked")
        expected_max = np.sqrt(2 * np.log(max(n_trials_tested, 2))) * 0.5
        deflated = float(sharpe - expected_max)
        if deflated < 0:
            notes.append("Deflated Sharpe approx negative after multiple-testing haircut")

    if abs(ac1) > 0.15:
        notes.append("Meaningful return autocorrelation — IID tests may be optimistic")
    if abs(kurt) > 3:
        notes.append("Fat tails — Sharpe CI may understate risk")

    return StatisticalResult(
        n_obs=n,
        sharpe=sharpe,
        sharpe_ci_low=ci_low,
        sharpe_ci_high=ci_high,
        mean_return_pvalue=float(pval),
        skewness=skew,
        excess_kurtosis=kurt,
        autocorrelation_lag1=ac1,
        n_trials_tested=n_trials_tested,
        deflated_sharpe_approx=deflated,
        multiple_testing_warning=multiple,
        notes=notes,
        bootstrap_sharpes=boot_arr.tolist()[:50],  # store sample, not all
    )

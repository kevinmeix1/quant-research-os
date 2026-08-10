"""Portfolio construction and stress testing (deterministic)."""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd
from pydantic import BaseModel, Field

from quant_research_os.engine.metrics import calculate_metrics


class PortfolioAllocation(BaseModel):
    method: str
    weights: dict[str, float]
    metrics: dict[str, float] = Field(default_factory=dict)
    risk_contributions: dict[str, float] = Field(default_factory=dict)
    notes: list[str] = Field(default_factory=list)


class StressResult(BaseModel):
    scenario: str
    metrics: dict[str, float]
    breached_limits: list[str] = Field(default_factory=list)
    decision: str = "PASS"


def allocate_portfolio(
    returns: dict[str, pd.Series],
    *,
    method: str = "volatility_scaling",
    max_weight: float = 0.5,
) -> PortfolioAllocation:
    df = pd.DataFrame(returns).dropna(how="any")
    notes: list[str] = []
    if df.empty or df.shape[1] == 0:
        return PortfolioAllocation(method=method, weights={}, notes=["empty returns"])

    cols = list(df.columns)
    if method == "equal_weight":
        w = np.repeat(1.0 / len(cols), len(cols))
    elif method == "risk_parity":
        vol = df.std(ddof=0).replace(0, np.nan)
        inv = 1.0 / vol
        inv = inv.fillna(0.0)
        w = (inv / inv.sum()).to_numpy() if inv.sum() else np.repeat(1.0 / len(cols), len(cols))
        notes.append("Inverse-vol risk parity (diagonal approximation)")
    elif method == "mean_variance":
        mu = df.mean().to_numpy()
        cov = df.cov().to_numpy()
        try:
            inv = np.linalg.pinv(cov)
            raw = inv @ mu
            raw = np.clip(raw, 0, None)
            w = raw / raw.sum() if raw.sum() > 0 else np.repeat(1.0 / len(cols), len(cols))
        except Exception:
            w = np.repeat(1.0 / len(cols), len(cols))
            notes.append("Mean-variance failed — fell back to equal weight")
    else:  # volatility_scaling
        vol = df.std(ddof=0).replace(0, np.nan)
        inv = 1.0 / vol
        inv = inv.fillna(0.0)
        w = (inv / inv.sum()).to_numpy() if inv.sum() else np.repeat(1.0 / len(cols), len(cols))

    w = np.clip(w, 0, max_weight)
    if w.sum() <= 0:
        w = np.repeat(1.0 / len(cols), len(cols))
    w = w / w.sum()
    weights = {c: float(wi) for c, wi in zip(cols, w)}

    port = (df * pd.Series(weights)).sum(axis=1)
    m = calculate_metrics(port)
    # Marginal risk contribution approx: w_i * (Cov w)_i / portfolio var
    cov = df.cov().to_numpy()
    w_arr = np.array([weights[c] for c in cols])
    port_var = float(w_arr @ cov @ w_arr)
    rc = {}
    if port_var > 0:
        mcr = cov @ w_arr
        for i, c in enumerate(cols):
            rc[c] = float(w_arr[i] * mcr[i] / port_var)

    return PortfolioAllocation(
        method=method,
        weights=weights,
        metrics=m.model_dump(exclude_none=True),
        risk_contributions=rc,
        notes=notes,
    )


def run_stress_tests(
    returns: pd.Series,
    *,
    max_drawdown_limit: float = -0.25,
    vol_limit: float = 0.35,
) -> list[StressResult]:
    r = pd.Series(returns, dtype=float).dropna()
    scenarios = {
        "volatility_doubles": r * 2.0,
        "returns_halved": r * 0.5,
        "worst_month_amplified": _amplify_worst(r, 2.0),
        "correlation_crisis_proxy": r.clip(upper=0) * 1.5 + r.clip(lower=0) * 0.5,
    }
    out: list[StressResult] = []
    for name, series in scenarios.items():
        m = calculate_metrics(series)
        breaches = []
        if m.max_drawdown < max_drawdown_limit:
            breaches.append(f"drawdown {m.max_drawdown:.2%} < limit {max_drawdown_limit:.2%}")
        if m.volatility > vol_limit:
            breaches.append(f"vol {m.volatility:.2%} > limit {vol_limit:.2%}")
        out.append(
            StressResult(
                scenario=name,
                metrics=m.model_dump(exclude_none=True),
                breached_limits=breaches,
                decision="REJECT" if breaches else "PASS",
            )
        )
    return out


def _amplify_worst(r: pd.Series, factor: float) -> pd.Series:
    out = r.copy()
    if out.empty:
        return out
    # amplify worst 5% of days
    q = out.quantile(0.05)
    out = out.where(out > q, out * factor)
    return out

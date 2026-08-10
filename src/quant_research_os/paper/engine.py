"""Paper trading simulation + monitoring (no real money)."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

import numpy as np
import pandas as pd

from quant_research_os.alpha.registry import AlphaRegistry
from quant_research_os.engine.metrics import calculate_metrics
from quant_research_os.storage.db import ResearchDB


def start_paper_trading(db: ResearchDB, alpha_id: str) -> dict[str, Any]:
    payload = {
        "alpha_id": alpha_id,
        "started_at": datetime.now(timezone.utc).isoformat(),
        "status": "PAPER_TRADING",
        "equity": [1.0],
        "alerts": [],
        "expected_sharpe": None,
    }
    reg = AlphaRegistry(db)
    alpha = reg.get(alpha_id)
    if alpha:
        payload["expected_sharpe"] = (alpha.metrics or {}).get("sharpe")
        payload["expected_metrics"] = alpha.metrics
    db.upsert_json("paper_strategies", "alpha_id", alpha_id, payload, status="PAPER_TRADING")
    return payload


def simulate_paper_step(db: ResearchDB, alpha_id: str, n_days: int = 21, seed: int = 0) -> dict[str, Any]:
    """Advance paper book with noisy version of historical return distribution."""
    raw = db.get_json("paper_strategies", "alpha_id", alpha_id)
    if not raw:
        raise KeyError(alpha_id)
    reg = AlphaRegistry(db)
    alpha = reg.get(alpha_id)
    hist = (alpha.robustness or {}).get("returns") if alpha else None
    rng = np.random.default_rng(seed)
    if hist:
        mu, sigma = float(np.mean(hist)), float(np.std(hist) + 1e-8)
    else:
        mu, sigma = 0.0, 0.01
    shocks = rng.normal(mu, sigma, size=n_days)
    equity = list(raw.get("equity") or [1.0])
    for r in shocks:
        equity.append(equity[-1] * (1 + float(r)))
    paper_rets = pd.Series(np.diff(equity) / np.array(equity[:-1]))
    live_metrics = calculate_metrics(paper_rets)
    expected = raw.get("expected_sharpe")
    alerts = list(raw.get("alerts") or [])
    if expected is not None and live_metrics.sharpe < (expected - 1.0):
        alerts.append(
            {
                "type": "performance_degradation",
                "at": datetime.now(timezone.utc).isoformat(),
                "detail": f"paper sharpe {live_metrics.sharpe:.2f} vs expected {expected:.2f}",
            }
        )
    raw.update(
        {
            "equity": equity,
            "alerts": alerts,
            "live_metrics": live_metrics.model_dump(),
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }
    )
    status = "DEGRADED" if alerts else "PAPER_TRADING"
    raw["status"] = status
    db.upsert_json("paper_strategies", "alpha_id", alpha_id, raw, status=status)
    if alerts and alpha:
        from quant_research_os.domain.enums import AlphaStatus

        alpha.status = AlphaStatus.DEGRADED
        # allow metrics already set
        reg.save(alpha)
    return raw


def list_paper(db: ResearchDB) -> list[dict[str, Any]]:
    return db.list_json("paper_strategies")

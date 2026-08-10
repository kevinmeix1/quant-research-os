"""Deterministic data quality checks."""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum

import numpy as np
import pandas as pd
from pydantic import BaseModel, Field


class DataQualitySeverity(str, Enum):
    OK = "OK"
    WARN = "WARN"
    BLOCK = "BLOCK"


class DataQualityIssue(BaseModel):
    check: str
    severity: DataQualitySeverity
    message: str
    count: int = 0


class DataQualityReport(BaseModel):
    dataset_id: str
    generated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    n_rows: int
    n_instruments: int
    date_start: str | None = None
    date_end: str | None = None
    issues: list[DataQualityIssue] = Field(default_factory=list)
    overall: DataQualitySeverity = DataQualitySeverity.OK

    @property
    def is_blocking(self) -> bool:
        return self.overall == DataQualitySeverity.BLOCK


def profile_price_panel(prices: pd.DataFrame, dataset_id: str = "prices") -> DataQualityReport:
    """Run deterministic quality checks on a wide price panel."""
    issues: list[DataQualityIssue] = []
    px = prices.sort_index()

    if px.index.has_duplicates:
        issues.append(
            DataQualityIssue(
                check="duplicate_timestamps",
                severity=DataQualitySeverity.BLOCK,
                message="Index contains duplicate timestamps",
                count=int(px.index.duplicated().sum()),
            )
        )

    if px.columns.duplicated().any():
        issues.append(
            DataQualityIssue(
                check="duplicate_instruments",
                severity=DataQualitySeverity.BLOCK,
                message="Duplicate instrument columns",
                count=int(px.columns.duplicated().sum()),
            )
        )

    missing = int(px.isna().sum().sum())
    if missing:
        frac = missing / max(px.size, 1)
        sev = DataQualitySeverity.BLOCK if frac > 0.2 else DataQualitySeverity.WARN
        issues.append(
            DataQualityIssue(
                check="missing_values",
                severity=sev,
                message=f"Missing values fraction={frac:.2%}",
                count=missing,
            )
        )

    # Stale prices: unchanged for >= 10 consecutive bars
    stale_count = 0
    for col in px.columns:
        unchanged = px[col].diff().fillna(0.0).eq(0.0)
        # streak length via groupby on breaks
        groups = (~unchanged).cumsum()
        streaks = unchanged.groupby(groups).sum()
        stale_count += int((streaks >= 10).sum())
    if stale_count:
        issues.append(
            DataQualityIssue(
                check="stale_prices",
                severity=DataQualitySeverity.WARN,
                message="Detected long unchanged-price streaks",
                count=stale_count,
            )
        )

    # Abnormal jumps: |return| > 25%
    rets = px.pct_change()
    jumps = int((rets.abs() > 0.25).sum().sum())
    if jumps:
        issues.append(
            DataQualityIssue(
                check="abnormal_jumps",
                severity=DataQualitySeverity.WARN,
                message="Absolute returns > 25% detected",
                count=jumps,
            )
        )

    # Non-monotonic / unsorted index
    if not px.index.is_monotonic_increasing:
        issues.append(
            DataQualityIssue(
                check="timestamp_order",
                severity=DataQualitySeverity.BLOCK,
                message="Index is not monotonic increasing",
            )
        )

    # Non-positive prices
    nonpos = int((px <= 0).sum().sum())
    if nonpos:
        issues.append(
            DataQualityIssue(
                check="non_positive_prices",
                severity=DataQualitySeverity.BLOCK,
                message="Non-positive prices found",
                count=nonpos,
            )
        )

    overall = DataQualitySeverity.OK
    if any(i.severity == DataQualitySeverity.BLOCK for i in issues):
        overall = DataQualitySeverity.BLOCK
    elif any(i.severity == DataQualitySeverity.WARN for i in issues):
        overall = DataQualitySeverity.WARN

    return DataQualityReport(
        dataset_id=dataset_id,
        n_rows=len(px),
        n_instruments=px.shape[1],
        date_start=str(px.index.min()) if len(px) else None,
        date_end=str(px.index.max()) if len(px) else None,
        issues=issues,
        overall=overall,
    )


def validate_ohlc(ohlc: pd.DataFrame) -> list[DataQualityIssue]:
    """Check impossible OHLC relationships when columns exist."""
    issues: list[DataQualityIssue] = []
    cols = {c.lower(): c for c in ohlc.columns}
    needed = {"open", "high", "low", "close"}
    if not needed.issubset(cols):
        return issues
    o, h, l, c = (ohlc[cols[k]] for k in ("open", "high", "low", "close"))
    bad = ((h < l) | (h < o) | (h < c) | (l > o) | (l > c)).sum()
    if hasattr(bad, "sum"):
        bad = int(bad.sum()) if not np.isscalar(bad) else int(bad)
    else:
        bad = int(bad)
    if bad:
        issues.append(
            DataQualityIssue(
                check="impossible_ohlc",
                severity=DataQualitySeverity.BLOCK,
                message="OHLC relationship violations",
                count=bad,
            )
        )
    return issues

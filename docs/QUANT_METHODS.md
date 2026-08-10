# QUANT_METHODS

## Cross-sectional backtest

1. Signal at close `t` from past prices only
2. Execute at bar `t + execution_lag` (`lag >= 1`)
3. Earn that bar’s close-to-close return on beginning weights
4. Drift fixed shares, then **NAV-renormalize** to weights
5. Turnover = `0.5 * Σ|Δw|` in weight space; costs subtracted from returns

## Metrics

Pinned local implementation:

- volatility / Sharpe use population std (`ddof=0`)
- Sortino uses full-sample downside deviation `sqrt(mean(min(r,0)^2))`
- annualization factor default 252

## Walk-forward

Frozen exogenous rule evaluated on expanding/rolling segments.
Overlapping OOS bars are deduplicated chronologically for aggregate metrics.
Parameter surfaces are full-sample diagnostics — not nested OOS fits.

## Regimes

Labels shifted by 1 bar to avoid same-day attribution leakage.

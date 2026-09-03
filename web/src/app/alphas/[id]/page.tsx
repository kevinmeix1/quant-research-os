"use client";

import { useMemo, useState } from "react";
import { useParams } from "next/navigation";
import useSWR from "swr";
import Link from "next/link";
import { api, formatNum } from "@/lib/api";
import {
  Badge,
  Button,
  Metric,
  Panel,
  SourceBanner,
  ErrorState,
} from "@/components/ui/primitives";
import {
  TimeSeriesChart,
  syntheticEquity,
} from "@/components/charts/TimeSeriesChart";

const TABS = [
  "Overview",
  "Thesis",
  "Performance",
  "Risk",
  "Robustness",
  "Regimes",
  "Correlations",
  "Portfolio",
  "Lineage",
  "Versions",
] as const;

export default function AlphaDetailPage() {
  const { id } = useParams<{ id: string }>();
  const [tab, setTab] = useState<(typeof TABS)[number]>("Overview");
  const { data, error, mutate } = useSWR(id ? `alpha-${id}` : null, () =>
    api.getAlpha(id),
  );
  const { data: corr } = useSWR("alpha-corr", () => api.portfolioCorrelations(), {
    shouldRetryOnError: false,
  });

  const equity = useMemo(
    () => syntheticEquity(data?.metrics?.sharpe as number | undefined, 160),
    [data],
  );

  if (error) {
    return (
      <div className="page">
        <ErrorState
          title="Alpha not found"
          message={
            error instanceof Error
              ? error.message
              : `Alpha ${id} is not in the library.`
          }
          actions={
            <>
              <Button onClick={() => void mutate()}>Retry</Button>
              <Link href="/alphas">
                <Button>Alpha Library</Button>
              </Link>
            </>
          }
        />
      </div>
    );
  }

  if (!data) {
    return (
      <div className="page">
        <div className="skeleton" style={{ width: 200 }} />
      </div>
    );
  }

  const m = data.metrics ?? {};

  return (
    <div className="page page-wide">
      <header className="page-header">
        <div>
          <div style={{ display: "flex", gap: 8, alignItems: "center" }}>
            <span className="mono" style={{ color: "var(--accent-text)" }}>
              {data.alpha_id}
            </span>
            <Badge status={String(data.status)} />
            <SourceBanner mode="BACKTEST" />
          </div>
          <h1 className="page-title" style={{ marginTop: 6, fontSize: 18 }}>
            {data.hypothesis ?? data.strategy_id ?? "Alpha"}
          </h1>
          <p className="page-subtitle">
            Strategy {data.strategy_id ?? "—"}
            {data.metrics_source_ids?.length
              ? ` · Provenance: ${data.metrics_source_ids.join(", ")}`
              : " · Metrics require source experiment ids"}
          </p>
        </div>
        <div className="page-actions">
          <Link href={`/portfolio?add=${data.alpha_id}`}>
            <Button variant="primary" size="sm">
              What-if in portfolio
            </Button>
          </Link>
        </div>
      </header>

      <div className="tabs" role="tablist">
        {TABS.map((t) => (
          <button
            key={t}
            type="button"
            role="tab"
            aria-selected={tab === t}
            className={`tab${tab === t ? " active" : ""}`}
            onClick={() => setTab(t)}
          >
            {t}
          </button>
        ))}
      </div>

      <div style={{ marginTop: 16 }} className="stack">
        {tab === "Overview" && (
          <div className="grid-4">
            <Panel title="Metrics">
              <div className="grid-2" style={{ gap: 12 }}>
                <Metric label="Sharpe" value={formatNum(m.sharpe as number)} />
                <Metric label="OOS Sharpe" value={formatNum(m.oos_sharpe as number)} />
                <Metric label="Drawdown" value={formatNum(m.max_drawdown as number)} />
                <Metric label="Turnover" value={formatNum(m.turnover as number)} />
              </div>
            </Panel>
            <Panel title="Quality">
              <div className="grid-2" style={{ gap: 12 }}>
                <Metric
                  label="Correlation"
                  value={formatNum(data.correlation_to_existing ?? undefined)}
                />
                <Metric
                  label="Robustness"
                  value={formatNum(data.robustness_score ?? undefined)}
                />
                <Metric
                  label="Regime stability"
                  value={formatNum(data.regime_stability ?? undefined)}
                />
                <Metric label="Status" value={String(data.status)} small />
              </div>
            </Panel>
            <Panel title="Economic Thesis">
              <p style={{ fontSize: 13, margin: 0 }}>
                {data.hypothesis ?? "No thesis text stored on this alpha."}
              </p>
            </Panel>
          </div>
        )}

        {tab === "Thesis" && (
          <Panel title="Economic Thesis">
            <p style={{ fontSize: 13 }}>{data.hypothesis ?? "—"}</p>
            <div className="metric-label" style={{ marginTop: 16 }}>
              Formula / Features
            </div>
            <pre style={{ fontSize: 11, color: "var(--text-2)" }}>
              {JSON.stringify(
                {
                  strategy_id: data.strategy_id,
                  parameters: data.parameters ?? null,
                },
                null,
                2,
              )}
            </pre>
          </Panel>
        )}

        {tab === "Performance" && (
          <Panel title="Performance">
            <TimeSeriesChart
              series={[{ name: "Equity (from metrics)", values: equity }]}
              height={260}
            />
          </Panel>
        )}

        {tab === "Risk" && (
          <Panel title="Risk">
            <div className="grid-3">
              <Metric label="Volatility" value={formatNum(m.ann_vol as number)} />
              <Metric label="Max DD" value={formatNum(m.max_drawdown as number)} />
              <Metric label="Sortino" value={formatNum(m.sortino as number)} />
            </div>
          </Panel>
        )}

        {tab === "Robustness" && (
          <Panel title="Robustness">
            <Metric
              label="Score"
              value={formatNum(data.robustness_score ?? (m.robustness as number))}
            />
            <p style={{ fontSize: 12, color: "var(--text-2)" }}>
              Parameter sensitivity and adversarial findings attach via research
              lineage.
            </p>
          </Panel>
        )}

        {tab === "Regimes" && (
          <Panel title="Regime Stability">
            <Metric
              label="Stability"
              value={formatNum(data.regime_stability ?? undefined)}
            />
            <Link href="/regimes">
              <Button size="sm">Open Regime Workspace</Button>
            </Link>
          </Panel>
        )}

        {tab === "Correlations" && (
          <Panel title="Correlations">
            <Metric
              label="vs existing book"
              value={formatNum(data.correlation_to_existing ?? undefined)}
            />
            <pre style={{ fontSize: 10, color: "var(--text-3)", marginTop: 12 }}>
              {JSON.stringify(corr ?? { note: "correlation matrix from API" }, null, 2).slice(0, 1200)}
            </pre>
          </Panel>
        )}

        {tab === "Portfolio" && (
          <Panel title="Portfolio Contribution">
            <p style={{ fontSize: 13 }}>
              Open the portfolio what-if to compare book metrics with this alpha
              added.
            </p>
            <Link href={`/portfolio?add=${data.alpha_id}`}>
              <Button variant="primary" size="sm">
                Run what-if
              </Button>
            </Link>
          </Panel>
        )}

        {tab === "Lineage" && (
          <Panel title="Alpha Lineage">
            <div className="workflow-graph">
              {["Hypothesis", "Experiment", "Strategy", "Alpha", "Portfolio", "Report"].map(
                (n, i) => (
                  <div key={n} style={{ display: "contents" }}>
                    {i > 0 ? <span className="wf-edge">↓</span> : null}
                    <div className="wf-node" data-status="completed">
                      <span className="wf-node-name">{n}</span>
                      <span className="wf-node-meta">
                        {n === "Alpha"
                          ? data.alpha_id
                          : n === "Strategy"
                            ? data.strategy_id ?? "—"
                            : data.metrics_source_ids?.[0] ?? "—"}
                      </span>
                    </div>
                  </div>
                ),
              )}
            </div>
          </Panel>
        )}

        {tab === "Versions" && (
          <Panel title="Versions / Agent History">
            <p style={{ fontSize: 12, color: "var(--text-2)" }}>
              Version history tracks prompt, feature, and parameter revisions.
              Current record is the live library entry.
            </p>
          </Panel>
        )}
      </div>
    </div>
  );
}

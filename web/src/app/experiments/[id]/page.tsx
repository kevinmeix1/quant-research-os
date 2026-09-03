"use client";

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

export default function ExperimentDetailPage() {
  const { id } = useParams<{ id: string }>();
  const { data, error, mutate } = useSWR(id ? `exp-detail-${id}` : null, () =>
    api.getExperiment(id),
  );

  if (error) {
    return (
      <div className="page">
        <ErrorState
          title="Experiment failed to load"
          message={
            error instanceof Error
              ? error.message
              : `Experiment ${id} could not be retrieved.`
          }
          actions={
            <>
              <Button onClick={() => void mutate()}>Retry</Button>
              <Link href="/experiments">
                <Button>Back</Button>
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
        <div className="skeleton" style={{ width: 240 }} />
      </div>
    );
  }

  const m = data.metrics ?? {};
  const equity = syntheticEquity(m.sharpe as number | undefined);
  const dd = equity.map((v, i) => {
    const peak = Math.max(...equity.slice(0, i + 1));
    return v / peak - 1;
  });
  const rollingSharpe = equity.map((_, i) => {
    if (i < 20) return 0;
    return ((m.sharpe as number) ?? 0.5) * (0.85 + 0.3 * Math.sin(i / 11));
  });

  const cfg = (data.config ?? {}) as Record<string, unknown>;

  return (
    <div className="page page-wide">
      <header className="page-header">
        <div>
          <div style={{ display: "flex", gap: 8, alignItems: "center" }}>
            <span className="mono" style={{ color: "var(--accent-text)" }}>
              {data.experiment_id}
            </span>
            <Badge status={String(data.status)} />
            <SourceBanner mode="BACKTEST" />
          </div>
          <h1 className="page-title" style={{ marginTop: 6 }}>
            Experiment Detail
          </h1>
          <p className="page-subtitle">
            Strategy {data.strategy_id ?? "—"} · Hypothesis{" "}
            {data.hypothesis_id ?? "—"} · Research{" "}
            {data.research_id ? (
              <Link href={`/research/${data.research_id}`}>{data.research_id}</Link>
            ) : (
              "—"
            )}
          </p>
        </div>
      </header>

      <div className="stack">
        <div className="grid-2">
          <Panel title="Configuration">
            <div className="grid-2" style={{ gap: 12 }}>
              <Metric label="Dataset" value={String(data.dataset ?? cfg.dataset ?? "—")} small />
              <Metric label="Strategy" value={String(data.strategy_id ?? "—")} small />
              <Metric label="Costs" value={String(cfg.costs ?? "baseline")} small />
              <Metric label="Slippage" value={String(cfg.slippage ?? "model")} small />
              <Metric
                label="Train"
                value={String(cfg.train_period ?? data.period_start ?? "—")}
                small
              />
              <Metric
                label="Test"
                value={String(cfg.test_period ?? data.period_end ?? "—")}
                small
              />
            </div>
            {cfg.parameters ? (
              <pre
                style={{
                  marginTop: 12,
                  fontSize: 10,
                  color: "var(--text-2)",
                  whiteSpace: "pre-wrap",
                }}
              >
                {JSON.stringify(cfg.parameters, null, 2)}
              </pre>
            ) : null}
          </Panel>
          <Panel title="Validation">
            <div className="grid-2" style={{ gap: 12 }}>
              <Metric label="In-sample Sharpe" value={formatNum(m.sharpe as number)} />
              <Metric
                label="OOS Sharpe"
                value={formatNum(
                  (m.oos_sharpe as number) ?? (m.sharpe_oos as number),
                )}
              />
              <Metric label="Max drawdown" value={formatNum(m.max_drawdown as number)} />
              <Metric label="Turnover" value={formatNum(m.turnover as number)} />
            </div>
            <p style={{ fontSize: 11, color: "var(--text-3)", marginTop: 12 }}>
              Walk-forward and holdout splits are stored on the experiment when
              the validation engine runs.
            </p>
          </Panel>
        </div>

        <Panel title="Performance">
          <div className="grid-2">
            <TimeSeriesChart
              series={[
                { name: "Equity (illustrative from metrics)", values: equity },
                { name: "Drawdown", values: dd.map((v) => 1 + v) },
              ]}
              height={220}
            />
            <TimeSeriesChart
              series={[{ name: "Rolling Sharpe (illustrative)", values: rollingSharpe }]}
              height={220}
              yFormat={(v) => v.toFixed(2)}
            />
          </div>
          <p style={{ fontSize: 11, color: "var(--caution)", marginTop: 8 }}>
            Full equity curves load from /backtests/&lt;id&gt; when persisted. Chart
            above is metric-conditioned until series attach.
          </p>
        </Panel>

        <div className="grid-2">
          <Panel title="Positions">
            <p style={{ fontSize: 12, color: "var(--text-2)" }}>
              Historical positions stream from the backtest artifact. Open the
              linked backtest once `metrics_source_ids` resolve.
            </p>
          </Panel>
          <Panel title="Robustness">
            <div className="grid-2">
              <Metric
                label="Robustness"
                value={formatNum(m.robustness as number | undefined)}
              />
              <Metric
                label="Param sensitivity"
                value={formatNum(m.param_sensitivity as number | undefined)}
              />
            </div>
          </Panel>
        </div>
      </div>
    </div>
  );
}

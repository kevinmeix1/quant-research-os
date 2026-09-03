"use client";

import useSWR from "swr";
import Link from "next/link";
import { api, formatNum } from "@/lib/api";
import { Badge, Metric, Panel, SourceBanner } from "@/components/ui/primitives";

export default function RiskPage() {
  const { data: portfolio } = useSWR("risk-port", () => api.portfolio());
  const { data: risk } = useSWR("risk-detail", () => api.portfolioRisk());
  const { data: alphas } = useSWR("risk-alphas", () => api.listAlphas());

  const alerts = [
    {
      level: "HIGH",
      text: "No live VaR feed — risk engine uses research-time stress only.",
    },
    ...((alphas ?? [])
      .filter((a) => (a.correlation_to_existing ?? 0) > 0.6)
      .slice(0, 3)
      .map((a) => ({
        level: "MEDIUM",
        text: `${a.alpha_id} correlation to existing book is ${formatNum(a.correlation_to_existing ?? undefined)}.`,
      })) as Array<{ level: string; text: string }>),
  ];

  return (
    <div className="page">
      <header className="page-header">
        <div>
          <div style={{ display: "flex", gap: 8, alignItems: "center" }}>
            <h1 className="page-title">Risk Center</h1>
            <SourceBanner mode="BACKTEST" />
          </div>
          <p className="page-subtitle">
            Portfolio volatility, drawdown, leverage, concentration, exposures,
            correlations, and stress tests requiring attention.
          </p>
        </div>
      </header>

      <div className="stack">
        <div className="grid-4">
          <Panel title="Volatility">
            <Metric label="Portfolio vol" value="—" hint="awaiting construction" />
          </Panel>
          <Panel title="Drawdown">
            <Metric label="Current DD" value="—" />
          </Panel>
          <Panel title="Leverage">
            <Metric label="Gross" value="1.00" hint="equal-weight stub" />
          </Panel>
          <Panel title="Concentration">
            <Metric
              label="HHI (approx)"
              value={
                portfolio?.n_alphas
                  ? formatNum(1 / portfolio.n_alphas)
                  : "—"
              }
            />
          </Panel>
        </div>

        <div className="grid-2">
          <Panel title="Risks Requiring Attention" className="adversarial">
            {alerts.map((a, i) => (
              <div className="finding" key={i}>
                <div
                  className={
                    a.level === "HIGH" ? "severity-high" : "severity-medium"
                  }
                >
                  {a.level}
                </div>
                <div style={{ fontSize: 13 }}>{a.text}</div>
              </div>
            ))}
          </Panel>

          <Panel title="Stress / Paper Overlay">
            <pre
              style={{
                fontSize: 10,
                color: "var(--text-2)",
                whiteSpace: "pre-wrap",
                margin: 0,
              }}
            >
              {JSON.stringify(risk ?? { paper: [] }, null, 2).slice(0, 1600)}
            </pre>
            <Link href="/paper" style={{ fontSize: 12 }}>
              Open paper trading →
            </Link>
          </Panel>
        </div>

        <Panel title="Alpha Risk Contribution" dense>
          <div className="data-table-wrap">
            <table className="data-table">
              <thead>
                <tr>
                  <th>Alpha</th>
                  <th>Status</th>
                  <th>Sharpe</th>
                  <th>Corr</th>
                  <th>Marginal risk</th>
                </tr>
              </thead>
              <tbody>
                {(alphas ?? []).slice(0, 40).map((a) => (
                  <tr key={a.alpha_id}>
                    <td>
                      <Link href={`/alphas/${a.alpha_id}`}>{a.alpha_id}</Link>
                    </td>
                    <td className="text">
                      <Badge status={String(a.status)} />
                    </td>
                    <td>{formatNum(a.metrics?.sharpe as number)}</td>
                    <td>{formatNum(a.correlation_to_existing ?? undefined)}</td>
                    <td>—</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Panel>
      </div>
    </div>
  );
}

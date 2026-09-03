"use client";

import useSWR from "swr";
import { api, formatNum } from "@/lib/api";
import { Badge, Metric, Panel, SourceBanner } from "@/components/ui/primitives";

const REGIMES = [
  { id: "low_vol", label: "Low Volatility", active: false },
  { id: "high_vol", label: "High Volatility", active: true },
  { id: "risk_on", label: "Risk-On", active: false },
  { id: "risk_off", label: "Risk-Off", active: false },
  { id: "trend", label: "Trending", active: false },
];

export default function RegimesPage() {
  const { data: alphas } = useSWR("regime-alphas", () => api.listAlphas());
  const [active] = REGIMES.filter((r) => r.active);

  return (
    <div className="page">
      <header className="page-header">
        <div>
          <div style={{ display: "flex", gap: 8, alignItems: "center" }}>
            <h1 className="page-title">Regimes</h1>
            <SourceBanner mode="BACKTEST" />
          </div>
          <p className="page-subtitle">
            Current regime, historical transitions, and strategy performance by
            regime. Select a regime to see which alphas historically worked best.
          </p>
        </div>
      </header>

      <div className="stack">
        <div className="grid-3">
          <Panel title="Current Regime">
            <Metric label="Active" value={active?.label ?? "—"} />
            <p style={{ fontSize: 11, color: "var(--text-3)", marginTop: 8 }}>
              Labels are shifted 1 bar in the regime engine to avoid look-ahead.
            </p>
          </Panel>
          <Panel title="Transitions">
            <ul className="timeline">
              {[
                ["2024-Q3", "Risk-On → High Vol"],
                ["2023-Q1", "Trend → Risk-Off"],
                ["2022-Q2", "Low Vol → High Vol"],
              ].map(([t, text]) => (
                <li key={t}>
                  <span className="timeline-time">{t}</span>
                  <span className="timeline-dot" />
                  <span className="timeline-text">{text}</span>
                </li>
              ))}
            </ul>
          </Panel>
          <Panel title="Historical Regimes">
            <div className="stack" style={{ gap: 6 }}>
              {REGIMES.map((r) => (
                <div
                  key={r.id}
                  style={{
                    display: "flex",
                    justifyContent: "space-between",
                    fontSize: 12,
                    padding: "4px 0",
                    borderBottom: "1px solid var(--border-0)",
                  }}
                >
                  <span>{r.label}</span>
                  {r.active ? <Badge status="running">current</Badge> : null}
                </div>
              ))}
            </div>
          </Panel>
        </div>

        <Panel title={`Alphas in ${active?.label ?? "regime"}`} dense>
          <div className="data-table-wrap">
            <table className="data-table">
              <thead>
                <tr>
                  <th>Alpha</th>
                  <th>Status</th>
                  <th>Sharpe</th>
                  <th>Regime stability</th>
                  <th>Sharpe in regime</th>
                </tr>
              </thead>
              <tbody>
                {(alphas ?? [])
                  .slice()
                  .sort(
                    (a, b) =>
                      (b.regime_stability ?? 0) - (a.regime_stability ?? 0),
                  )
                  .slice(0, 30)
                  .map((a) => (
                    <tr key={a.alpha_id}>
                      <td>{a.alpha_id}</td>
                      <td className="text">
                        <Badge status={String(a.status)} />
                      </td>
                      <td>{formatNum(a.metrics?.sharpe as number)}</td>
                      <td>{formatNum(a.regime_stability ?? undefined)}</td>
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

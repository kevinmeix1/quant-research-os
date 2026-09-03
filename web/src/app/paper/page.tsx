"use client";

import useSWR from "swr";
import { api, formatNum } from "@/lib/api";
import {
  Badge,
  Button,
  EmptyState,
  Metric,
  Panel,
  SourceBanner,
} from "@/components/ui/primitives";

export default function PaperTradingPage() {
  const { data, mutate, isLoading } = useSWR("paper", () => api.listPaper(), {
    refreshInterval: 10000,
  });

  return (
    <div className="page">
      <header className="page-header">
        <div>
          <div style={{ display: "flex", gap: 8, alignItems: "center" }}>
            <h1 className="page-title">Paper Trading</h1>
            <SourceBanner mode="PAPER TRADING" />
          </div>
          <p className="page-subtitle">
            Paper portfolio, positions, fills, P&amp;L, slippage, and expected vs
            realized performance. Never confuse with{" "}
            <SourceBanner mode="BACKTEST" /> or <SourceBanner mode="LIVE" />.
          </p>
        </div>
      </header>

      <div
        style={{
          display: "flex",
          gap: 8,
          marginBottom: 16,
          padding: 10,
          border: "1px solid rgba(168,85,247,0.35)",
          background: "rgba(168,85,247,0.06)",
          fontSize: 12,
        }}
      >
        <strong>Mode: PAPER TRADING</strong>
        <span style={{ color: "var(--text-2)" }}>
          Simulation may use IID noise from backtest μ/σ — labeled in payload.
          Not live execution.
        </span>
      </div>

      <div className="stack">
        <div className="grid-3">
          <Panel title="Paper Portfolio">
            <Metric label="Strategies" value={data?.length ?? "—"} />
          </Panel>
          <Panel title="Expected vs Realized">
            <p style={{ fontSize: 12, color: "var(--text-2)", margin: 0 }}>
              Compare expected Sharpe from research against paper path.
            </p>
          </Panel>
          <Panel title="Controls">
            <Button
              size="sm"
              disabled={!data?.[0]}
              onClick={() => {
                const id = data?.[0]?.alpha_id;
                if (!id) return;
                void api.paperStep(id, 21).then(() => mutate());
              }}
            >
              Step first strategy (+21d)
            </Button>
          </Panel>
        </div>

        <Panel title="Positions / Fills" dense>
          {isLoading ? (
            <div className="panel-body">
              <div className="skeleton" style={{ width: "40%" }} />
            </div>
          ) : !data?.length ? (
            <EmptyState
              title="No paper strategies"
              description="Promote a robust alpha to paper trading from the research report survivors."
            />
          ) : (
            <div className="data-table-wrap">
              <table className="data-table">
                <thead>
                  <tr>
                    <th>Alpha</th>
                    <th>Mode</th>
                    <th>P&amp;L</th>
                    <th>Expected Sharpe</th>
                    <th>Realized Sharpe</th>
                    <th>Slippage</th>
                    <th>Status</th>
                    <th></th>
                  </tr>
                </thead>
                <tbody>
                  {data.map((p) => (
                    <tr key={p.alpha_id}>
                      <td>{p.alpha_id}</td>
                      <td className="text">
                        <Badge status="paper">PAPER</Badge>
                      </td>
                      <td>{formatNum(p.pnl)}</td>
                      <td>{formatNum(p.expected_sharpe)}</td>
                      <td>{formatNum(p.realized_sharpe)}</td>
                      <td>{formatNum(p.slippage)}</td>
                      <td>{String(p.status ?? "—")}</td>
                      <td className="text">
                        <Button
                          size="sm"
                          onClick={() =>
                            void api.paperStep(p.alpha_id, 5).then(() => mutate())
                          }
                        >
                          Step
                        </Button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </Panel>
      </div>
    </div>
  );
}

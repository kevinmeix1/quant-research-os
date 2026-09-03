"use client";

import { Panel, Metric, SourceBanner } from "@/components/ui/primitives";

export default function MarketDataPage() {
  return (
    <div className="page">
      <header className="page-header">
        <div>
          <div style={{ display: "flex", gap: 8, alignItems: "center" }}>
            <h1 className="page-title">Market Data</h1>
            <SourceBanner mode="BACKTEST" />
          </div>
          <p className="page-subtitle">
            Dataset inventory, coverage, and quality used by research agents.
          </p>
        </div>
      </header>
      <div className="grid-3">
        <Panel title="FX_G10">
          <div className="grid-2" style={{ gap: 10 }}>
            <Metric label="Coverage" value="2010–2026" small />
            <Metric label="Frequency" value="Daily" small />
            <Metric label="Quality" value="OK" small />
            <Metric label="Source" value="Synthetic / configured" small />
          </div>
        </Panel>
        <Panel title="Data Agent Checks">
          <ul style={{ margin: 0, paddingLeft: 16, fontSize: 12 }}>
            <li>Missing bars → fail experiment</li>
            <li>Execution lag ≥ 1 enforced</li>
            <li>Cost model baseline attached</li>
          </ul>
        </Panel>
        <Panel title="Universe">
          <p style={{ fontSize: 12, color: "var(--text-2)" }}>
            Cross-sectional FX G10 is the flagship universe. Additional datasets
            register through the data agent allowlist.
          </p>
        </Panel>
      </div>
    </div>
  );
}

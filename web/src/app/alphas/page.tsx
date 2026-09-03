"use client";

import { useMemo, useState } from "react";
import { useRouter } from "next/navigation";
import useSWR from "swr";
import { api, formatNum } from "@/lib/api";
import { Badge, Button, EmptyState, Panel } from "@/components/ui/primitives";
import { DataTable, type Column } from "@/components/ui/DataTable";
import type { Alpha } from "@/domain/types";

export default function AlphaLibraryPage() {
  const router = useRouter();
  const [q, setQ] = useState("");
  const [status, setStatus] = useState("ALL");
  const { data, error, isLoading } = useSWR("alphas-lib", () => api.listAlphas());

  const filtered = useMemo(() => {
    const needle = q.trim().toLowerCase();
    return (data ?? []).filter((a) => {
      if (status !== "ALL" && String(a.status).toUpperCase() !== status)
        return false;
      if (!needle) return true;
      return [a.alpha_id, a.strategy_id, a.hypothesis, a.status]
        .filter(Boolean)
        .some((v) => String(v).toLowerCase().includes(needle));
    });
  }, [data, q, status]);

  const columns: Column<Alpha>[] = [
    {
      key: "id",
      header: "Alpha",
      sortable: true,
      sortValue: (a) => a.alpha_id,
      render: (a) => (
        <span style={{ color: "var(--accent-text)" }}>{a.alpha_id}</span>
      ),
    },
    {
      key: "strategy",
      header: "Strategy",
      render: (a) => a.strategy_id ?? "—",
    },
    {
      key: "sharpe",
      header: "Sharpe",
      sortable: true,
      align: "right",
      sortValue: (a) => (a.metrics?.sharpe as number) ?? null,
      render: (a) => formatNum(a.metrics?.sharpe as number | undefined),
    },
    {
      key: "oos",
      header: "OOS Sharpe",
      sortable: true,
      align: "right",
      sortValue: (a) => (a.metrics?.oos_sharpe as number) ?? null,
      render: (a) => formatNum(a.metrics?.oos_sharpe as number | undefined),
    },
    {
      key: "dd",
      header: "Drawdown",
      align: "right",
      sortValue: (a) => (a.metrics?.max_drawdown as number) ?? null,
      render: (a) => formatNum(a.metrics?.max_drawdown as number | undefined),
    },
    {
      key: "to",
      header: "Turnover",
      align: "right",
      render: (a) => formatNum(a.metrics?.turnover as number | undefined),
    },
    {
      key: "corr",
      header: "Correlation",
      sortable: true,
      align: "right",
      sortValue: (a) => a.correlation_to_existing ?? null,
      render: (a) => formatNum(a.correlation_to_existing ?? undefined),
    },
    {
      key: "rob",
      header: "Robustness",
      align: "right",
      render: (a) => formatNum(a.robustness_score ?? undefined),
    },
    {
      key: "reg",
      header: "Regime Stability",
      align: "right",
      render: (a) => formatNum(a.regime_stability ?? undefined),
    },
    {
      key: "status",
      header: "Status",
      sortable: true,
      sortValue: (a) => String(a.status),
      render: (a) => <Badge status={String(a.status)} />,
    },
  ];

  return (
    <div className="page page-wide">
      <header className="page-header">
        <div>
          <h1 className="page-title">Alpha Library</h1>
          <p className="page-subtitle">
            Institutional alpha inventory with lifecycle status, correlation to
            existing book, and robustness posture.
          </p>
        </div>
        <div className="page-actions">
          <Button size="sm" onClick={() => router.push("/portfolio")}>
            Portfolio impact
          </Button>
        </div>
      </header>

      <div style={{ display: "flex", gap: 8, marginBottom: 12, flexWrap: "wrap" }}>
        <input
          className="command-input"
          style={{ maxWidth: 260 }}
          placeholder="Filter by id, strategy, thesis…"
          value={q}
          onChange={(e) => setQ(e.target.value)}
        />
        <select
          className="command-input"
          style={{ maxWidth: 180, width: 180 }}
          value={status}
          onChange={(e) => setStatus(e.target.value)}
        >
          {[
            "ALL",
            "ROBUST",
            "PROMISING",
            "CANDIDATE",
            "PAPER_TRADING",
            "REJECTED",
            "RETIRED",
          ].map((s) => (
            <option key={s} value={s}>
              {s}
            </option>
          ))}
        </select>
      </div>

      <Panel title="Alphas" dense>
        {isLoading ? (
          <div className="panel-body">
            <div className="skeleton" style={{ width: "40%" }} />
          </div>
        ) : error ? (
          <div className="panel-body">
            <p style={{ color: "var(--negative)", fontSize: 12 }}>
              Alpha library unavailable.
            </p>
          </div>
        ) : (
          <DataTable
            rows={filtered}
            columns={columns}
            rowKey={(a) => a.alpha_id}
            onRowClick={(a) => router.push(`/alphas/${a.alpha_id}`)}
            empty={
              <EmptyState
                title="No robust alphas yet"
                description='Start a research task: "Find a low-correlation strategy for my portfolio."'
                action={
                  <Button size="sm" onClick={() => router.push("/research")}>
                    Open Research
                  </Button>
                }
              />
            }
          />
        )}
      </Panel>
    </div>
  );
}

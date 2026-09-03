"use client";

import { useMemo, useState } from "react";
import { useRouter } from "next/navigation";
import useSWR from "swr";
import { api, formatNum } from "@/lib/api";
import { Badge, Button, EmptyState, Panel } from "@/components/ui/primitives";
import { DataTable, type Column } from "@/components/ui/DataTable";
import type { Experiment } from "@/domain/types";

export default function ExperimentsPage() {
  const router = useRouter();
  const [q, setQ] = useState("");
  const [status, setStatus] = useState("ALL");
  const { data, error, isLoading, mutate } = useSWR("experiments-all", () =>
    api.listExperiments(undefined, 500),
  );

  const filtered = useMemo(() => {
    const needle = q.trim().toLowerCase();
    return (data ?? []).filter((e) => {
      if (status !== "ALL" && String(e.status).toUpperCase() !== status)
        return false;
      if (!needle) return true;
      return [
        e.experiment_id,
        e.strategy_id,
        e.hypothesis_id,
        e.research_id,
        e.dataset,
      ]
        .filter(Boolean)
        .some((v) => String(v).toLowerCase().includes(needle));
    });
  }, [data, q, status]);

  const columns: Column<Experiment>[] = [
    {
      key: "id",
      header: "Experiment",
      sortable: true,
      sortValue: (e) => e.experiment_id,
      render: (e) => (
        <span style={{ color: "var(--accent-text)" }}>{e.experiment_id}</span>
      ),
    },
    {
      key: "strategy",
      header: "Strategy",
      sortable: true,
      sortValue: (e) => e.strategy_id ?? "",
      render: (e) => e.strategy_id ?? "—",
    },
    {
      key: "hyp",
      header: "Hypothesis",
      render: (e) => e.hypothesis_id ?? "—",
    },
    {
      key: "dataset",
      header: "Dataset",
      render: (e) => String(e.dataset ?? "—"),
    },
    {
      key: "sharpe",
      header: "Sharpe",
      sortable: true,
      align: "right",
      sortValue: (e) => (e.metrics?.sharpe as number) ?? null,
      render: (e) => formatNum(e.metrics?.sharpe as number | undefined),
    },
    {
      key: "ret",
      header: "Return",
      sortable: true,
      align: "right",
      sortValue: (e) => (e.metrics?.ann_return as number) ?? null,
      render: (e) => formatNum(e.metrics?.ann_return as number | undefined),
    },
    {
      key: "dd",
      header: "Drawdown",
      sortable: true,
      align: "right",
      sortValue: (e) => (e.metrics?.max_drawdown as number) ?? null,
      render: (e) => formatNum(e.metrics?.max_drawdown as number | undefined),
    },
    {
      key: "to",
      header: "Turnover",
      align: "right",
      sortValue: (e) => (e.metrics?.turnover as number) ?? null,
      render: (e) => formatNum(e.metrics?.turnover as number | undefined),
    },
    {
      key: "oos",
      header: "OOS Sharpe",
      align: "right",
      sortable: true,
      sortValue: (e) =>
        (e.metrics?.oos_sharpe as number) ??
        (e.metrics?.sharpe_oos as number) ??
        null,
      render: (e) =>
        formatNum(
          (e.metrics?.oos_sharpe as number) ??
            (e.metrics?.sharpe_oos as number | undefined),
        ),
    },
    {
      key: "status",
      header: "Status",
      sortable: true,
      sortValue: (e) => String(e.status),
      render: (e) => <Badge status={String(e.status)} />,
    },
  ];

  return (
    <div className="page page-wide">
      <header className="page-header">
        <div>
          <h1 className="page-title">Experiments</h1>
          <p className="page-subtitle">
            Sortable, filterable experiment ledger. Click a row for configuration,
            performance, validation, and robustness.
          </p>
        </div>
        <div className="page-actions">
          <Button size="sm" onClick={() => void mutate()}>
            Refresh
          </Button>
          <Button
            size="sm"
            onClick={() => {
              const blob = new Blob([JSON.stringify(filtered, null, 2)], {
                type: "application/json",
              });
              const url = URL.createObjectURL(blob);
              const a = document.createElement("a");
              a.href = url;
              a.download = "experiments.json";
              a.click();
              URL.revokeObjectURL(url);
            }}
          >
            Export
          </Button>
        </div>
      </header>

      <div
        style={{
          display: "flex",
          gap: 8,
          marginBottom: 12,
          flexWrap: "wrap",
        }}
      >
        <input
          className="command-input"
          style={{ maxWidth: 280 }}
          placeholder="Filter experiments…"
          value={q}
          onChange={(e) => setQ(e.target.value)}
          aria-label="Filter experiments"
        />
        <select
          className="command-input"
          style={{ maxWidth: 160, width: 160 }}
          value={status}
          onChange={(e) => setStatus(e.target.value)}
          aria-label="Status filter"
        >
          {["ALL", "COMPLETED", "FAILED", "REJECTED", "RUNNING", "PENDING"].map(
            (s) => (
              <option key={s} value={s}>
                {s}
              </option>
            ),
          )}
        </select>
        <span className="mono" style={{ fontSize: 11, color: "var(--text-3)", alignSelf: "center" }}>
          {filtered.length} rows · view: default
        </span>
      </div>

      <Panel title="Experiment Explorer" dense>
        {isLoading ? (
          <div className="panel-body">
            <div className="skeleton" style={{ width: "50%" }} />
          </div>
        ) : error ? (
          <div className="panel-body">
            <p style={{ color: "var(--negative)", fontSize: 12 }}>
              Failed to load experiments from API.
            </p>
          </div>
        ) : (
          <DataTable
            rows={filtered}
            columns={columns}
            rowKey={(e) => e.experiment_id}
            onRowClick={(e) => router.push(`/experiments/${e.experiment_id}`)}
            empty={
              <EmptyState
                title="No experiments"
                description="Run research to populate the experiment ledger."
              />
            }
          />
        )}
      </Panel>
    </div>
  );
}

"use client";

import { useRouter } from "next/navigation";
import useSWR from "swr";
import { api } from "@/lib/api";
import { EmptyState, Panel } from "@/components/ui/primitives";
import { DataTable, type Column } from "@/components/ui/DataTable";
import type { Strategy } from "@/domain/types";

export default function StrategiesPage() {
  const router = useRouter();
  const { data, isLoading } = useSWR("strategies", () => api.listStrategies());

  const columns: Column<Strategy>[] = [
    {
      key: "id",
      header: "Strategy",
      sortable: true,
      sortValue: (s) => s.strategy_id,
      render: (s) => (
        <span style={{ color: "var(--accent-text)" }}>{s.strategy_id}</span>
      ),
    },
    {
      key: "name",
      header: "Name",
      render: (s) => s.name ?? "—",
    },
    {
      key: "family",
      header: "Family",
      render: (s) => s.family ?? "—",
    },
    {
      key: "asset",
      header: "Asset class",
      render: (s) => s.asset_class ?? "—",
    },
  ];

  return (
    <div className="page page-wide">
      <header className="page-header">
        <div>
          <h1 className="page-title">Strategies</h1>
          <p className="page-subtitle">
            Strategy definitions underlying alphas — families, parameters, and
            asset class.
          </p>
        </div>
      </header>
      <Panel title="Strategy Registry" dense>
        {isLoading ? (
          <div className="panel-body">
            <div className="skeleton" style={{ width: "40%" }} />
          </div>
        ) : (
          <DataTable
            rows={data ?? []}
            columns={columns}
            rowKey={(s) => s.strategy_id}
            onRowClick={(s) => router.push(`/alphas?q=${s.strategy_id}`)}
            empty={
              <EmptyState
                title="No strategies"
                description="Strategies appear when research registers candidates."
              />
            }
          />
        )}
      </Panel>
    </div>
  );
}

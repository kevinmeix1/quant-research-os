"use client";

import Link from "next/link";
import useSWR from "swr";
import { api } from "@/lib/api";
import { Badge, Button, EmptyState, Panel } from "@/components/ui/primitives";
import { DataTable, type Column } from "@/components/ui/DataTable";
import type { ResearchRequest } from "@/domain/types";
import { useRouter } from "next/navigation";

export default function ResearchListPage() {
  const router = useRouter();
  const { data, isLoading, error, mutate } = useSWR("research-page", () =>
    api.listResearch(100),
  );

  const columns: Column<ResearchRequest & { id?: string }>[] = [
    {
      key: "id",
      header: "Research",
      sortable: true,
      sortValue: (r) => r.research_id,
      render: (r) => (
        <span style={{ color: "var(--accent-text)" }}>{r.research_id}</span>
      ),
    },
    {
      key: "q",
      header: "Question",
      render: (r) => (
        <span className="text truncate" style={{ maxWidth: 420, display: "inline-block" }}>
          {r.question}
        </span>
      ),
    },
    {
      key: "status",
      header: "Status",
      sortable: true,
      sortValue: (r) => String(r.status),
      render: (r) => <Badge status={String(r.status)} />,
    },
    {
      key: "univ",
      header: "Universe",
      render: (r) => String(r.universe ?? "—"),
    },
    {
      key: "created",
      header: "Created",
      sortable: true,
      sortValue: (r) => String(r.created_at ?? ""),
      render: (r) => String(r.created_at ?? "—").replace("T", " ").slice(0, 19),
    },
  ];

  return (
    <div className="page page-wide">
      <header className="page-header">
        <div>
          <h1 className="page-title">Research</h1>
          <p className="page-subtitle">
            Research runs are the unit of work. Open a run to inspect the
            workflow graph, hypotheses, experiments, and agent decisions.
          </p>
        </div>
        <div className="page-actions">
          <Button size="sm" onClick={() => void mutate()}>
            Refresh
          </Button>
        </div>
      </header>

      <Panel title="Research Runs" dense>
        {isLoading ? (
          <div className="panel-body">
            <div className="skeleton" style={{ width: "40%" }} />
          </div>
        ) : error ? (
          <div className="panel-body">
            <p style={{ color: "var(--negative)", fontSize: 12 }}>
              Failed to load research. Is the API running on :8002?
            </p>
          </div>
        ) : (
          <DataTable
            rows={data ?? []}
            columns={columns}
            rowKey={(r) => r.research_id}
            onRowClick={(r) => router.push(`/research/${r.research_id}`)}
            empty={
              <EmptyState
                title="No research runs yet"
                description='Use the command bar: "Find a robust cross-sectional FX strategy with low correlation to momentum."'
              />
            }
          />
        )}
      </Panel>
    </div>
  );
}

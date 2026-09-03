"use client";

import Link from "next/link";
import useSWR from "swr";
import { api } from "@/lib/api";
import { Badge, EmptyState, Panel } from "@/components/ui/primitives";

export default function ReportsPage() {
  const { data } = useSWR("reports-research", () => api.listResearch(100));
  const withReports = data ?? [];

  return (
    <div className="page">
      <header className="page-header">
        <div>
          <h1 className="page-title">Reports</h1>
          <p className="page-subtitle">
            Professional research reports with traceable numerical claims.
          </p>
        </div>
      </header>
      <Panel title="Research Reports" dense>
        {!withReports.length ? (
          <EmptyState
            title="No reports yet"
            description="Completed research runs publish reports with executive summary, validation, and adversarial review."
          />
        ) : (
          <div className="data-table-wrap">
            <table className="data-table">
              <thead>
                <tr>
                  <th>Research</th>
                  <th>Question</th>
                  <th>Status</th>
                  <th></th>
                </tr>
              </thead>
              <tbody>
                {withReports.map((r) => (
                  <tr key={r.research_id}>
                    <td>{r.research_id}</td>
                    <td className="text truncate" style={{ maxWidth: 360 }}>
                      {r.question}
                    </td>
                    <td className="text">
                      <Badge status={String(r.status)} />
                    </td>
                    <td className="text">
                      <Link href={`/reports/${r.research_id}`}>Open</Link>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </Panel>
    </div>
  );
}

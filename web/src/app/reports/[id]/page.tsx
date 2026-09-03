"use client";

import { useParams } from "next/navigation";
import useSWR from "swr";
import Link from "next/link";
import { api } from "@/lib/api";
import {
  Badge,
  Button,
  ErrorState,
  Panel,
  SourceBanner,
} from "@/components/ui/primitives";

const SECTIONS = [
  "Executive Summary",
  "Research Question",
  "Hypotheses",
  "Data",
  "Methodology",
  "Results",
  "Validation",
  "Robustness",
  "Regimes",
  "Diversification",
  "Risk",
  "Adversarial Review",
  "Conclusion",
];

export default function ReportViewerPage() {
  const { id } = useParams<{ id: string }>();
  const { data: detail, error } = useSWR(id ? `rep-detail-${id}` : null, () =>
    api.getResearch(id),
  );
  const { data: report } = useSWR(id ? `rep-${id}` : null, () => api.getReport(id), {
    shouldRetryOnError: false,
  });

  const doc = report ?? detail?.report;

  if (error && !doc) {
    return (
      <div className="page">
        <ErrorState
          title="Report unavailable"
          message={`No report for research ${id}. The run may still be in progress.`}
          actions={
            <Link href={`/research/${id}`}>
              <Button>Open research workspace</Button>
            </Link>
          }
        />
      </div>
    );
  }

  return (
    <div className="page">
      <header className="page-header">
        <div>
          <div style={{ display: "flex", gap: 8, alignItems: "center" }}>
            <span className="mono" style={{ color: "var(--accent-text)" }}>
              {id}
            </span>
            <Badge status={String(doc?.status ?? detail?.request?.status ?? "")} />
            <SourceBanner mode="BACKTEST" />
          </div>
          <h1 className="page-title" style={{ marginTop: 6 }}>
            Research Report
          </h1>
          <p className="page-subtitle">{detail?.request?.question}</p>
        </div>
        <div className="page-actions">
          <Button
            size="sm"
            onClick={() => window.print()}
          >
            Print / PDF
          </Button>
          <Button
            size="sm"
            onClick={() => {
              const blob = new Blob([JSON.stringify(doc, null, 2)], {
                type: "application/json",
              });
              const url = URL.createObjectURL(blob);
              const a = document.createElement("a");
              a.href = url;
              a.download = `report-${id}.json`;
              a.click();
              URL.revokeObjectURL(url);
            }}
          >
            Export
          </Button>
        </div>
      </header>

      <div className="stack">
        <Panel title="Executive Summary">
          <p style={{ fontSize: 14, lineHeight: 1.55, margin: 0 }}>
            {String(
              doc?.executive_summary ??
                "Report body will populate when the research orchestrator finishes.",
            )}
          </p>
        </Panel>

        {SECTIONS.slice(1).map((section) => {
          const key = section.toLowerCase().replace(/\s+/g, "_");
          const body =
            (doc?.sections as Record<string, unknown> | undefined)?.[key] ??
            (doc as Record<string, unknown> | null)?.[key];
          return (
            <Panel title={section} key={section}>
              {body == null ? (
                <p style={{ fontSize: 12, color: "var(--text-3)", margin: 0 }}>
                  Section pending or not emitted for this run.
                </p>
              ) : typeof body === "string" ? (
                <p style={{ fontSize: 13, margin: 0 }}>{body}</p>
              ) : (
                <pre
                  style={{
                    margin: 0,
                    fontSize: 11,
                    whiteSpace: "pre-wrap",
                    color: "var(--text-2)",
                  }}
                >
                  {JSON.stringify(body, null, 2)}
                </pre>
              )}
              {section === "Results" && Array.isArray(doc?.survivors) ? (
                <div style={{ marginTop: 12 }}>
                  <div className="metric-label">Survivors (traceable)</div>
                  <ul style={{ fontSize: 12 }}>
                    {(doc?.survivors as string[]).map((s) => (
                      <li key={s}>
                        <Link href={`/alphas/${s}`}>{s}</Link>
                      </li>
                    ))}
                  </ul>
                </div>
              ) : null}
            </Panel>
          );
        })}
      </div>
    </div>
  );
}

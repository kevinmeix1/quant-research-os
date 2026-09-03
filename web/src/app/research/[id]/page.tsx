"use client";

import { useMemo, useState } from "react";
import { useParams } from "next/navigation";
import useSWR from "swr";
import Link from "next/link";
import { api, formatNum } from "@/lib/api";
import {
  Badge,
  Button,
  EmptyState,
  Metric,
  Panel,
  SourceBanner,
} from "@/components/ui/primitives";
import {
  ResearchGraph,
  buildWorkflowFromTrace,
} from "@/components/research/ResearchGraph";
import type { WorkflowNode } from "@/domain/types";

export default function ResearchWorkspacePage() {
  const params = useParams<{ id: string }>();
  const id = params.id;
  const [selected, setSelected] = useState<WorkflowNode | null>(null);
  const [tab, setTab] = useState<"results" | "hypotheses" | "review">("results");

  const { data, error, isLoading, mutate } = useSWR(
    id ? `research-${id}` : null,
    () => api.getResearch(id),
    { refreshInterval: 5000 },
  );
  const { data: trace } = useSWR(
    id ? `trace-${id}` : null,
    () => api.getTrace(id),
    { refreshInterval: 5000 },
  );
  const { data: experiments } = useSWR(
    id ? `exp-${id}` : null,
    () => api.listExperiments(id, 500),
    { refreshInterval: 5000 },
  );

  const nodes = useMemo(
    () =>
      buildWorkflowFromTrace(
        trace ?? [],
        String(data?.request?.status ?? data?.report?.status ?? ""),
      ),
    [trace, data],
  );

  const plan = data?.plan;
  const report = data?.report;
  const req = data?.request;

  const agentDetail = useMemo(() => {
    if (!selected || !trace) return null;
    const related = trace.filter((t) => {
      const a = (t.agent ?? t.event ?? "").toLowerCase();
      return a.includes(selected.id) || a.includes(selected.label.toLowerCase().split(" ")[0]);
    });
    return related.slice(-5);
  }, [selected, trace]);

  if (isLoading) {
    return (
      <div className="page">
        <div className="skeleton" style={{ width: 280, marginBottom: 12 }} />
        <div className="skeleton" style={{ width: "80%", height: 60 }} />
      </div>
    );
  }

  if (error || !req) {
    return (
      <div className="page">
        <div className="error-state">
          <h3>Research not found</h3>
          <p>
            {error instanceof Error
              ? error.message
              : `No research run with id ${id}.`}
          </p>
          <div className="error-actions">
            <Link href="/research">
              <Button>Back to Research</Button>
            </Link>
            <Button onClick={() => void mutate()}>Retry</Button>
          </div>
        </div>
      </div>
    );
  }

  const hypotheses = (plan?.hypotheses as Array<Record<string, unknown>>) ?? [];

  return (
    <div className="page page-wide">
      <header className="page-header">
        <div>
          <div style={{ display: "flex", gap: 8, alignItems: "center", marginBottom: 6 }}>
            <span className="mono" style={{ color: "var(--accent-text)", fontSize: 12 }}>
              {req.research_id}
            </span>
            <Badge status={String(req.status)} />
            <SourceBanner mode="BACKTEST" />
          </div>
          <h1 className="page-title" style={{ fontSize: 18 }}>
            {req.question}
          </h1>
          <p className="page-subtitle">
            Created {String(req.created_at ?? "—").replace("T", " ").slice(0, 19)}
            {" · "}
            Budget {String(req.max_experiments ?? "—")} experiments
            {" · "}
            Universe {String(req.universe ?? "—")}
          </p>
        </div>
        <div className="page-actions">
          <Button
            size="sm"
            variant="danger"
            onClick={() => void api.cancelResearch(id).then(() => mutate())}
          >
            Cancel
          </Button>
          {report ? (
            <Link href={`/reports/${id}`}>
              <Button size="sm" variant="primary">
                Open Report
              </Button>
            </Link>
          ) : null}
        </div>
      </header>

      <div className="research-layout">
        <Panel title="Research Question">
          <div className="stack" style={{ gap: 14 }}>
            <div>
              <div className="metric-label">Original question</div>
              <div style={{ marginTop: 4 }}>{req.question}</div>
            </div>
            {plan?.interpreted_question ? (
              <div>
                <div className="metric-label">
                  System interpretation <Badge status="inferred">inferred</Badge>
                </div>
                <div style={{ marginTop: 4 }}>{plan.interpreted_question}</div>
              </div>
            ) : null}
            <div className="grid-3">
              <div>
                <div className="metric-label">Objectives</div>
                <ul style={{ margin: "6px 0 0", paddingLeft: 16, fontSize: 12 }}>
                  {(plan?.objectives as string[] | undefined)?.map((o) => (
                    <li key={o}>{o}</li>
                  )) ?? <li style={{ color: "var(--text-3)" }}>Pending plan</li>}
                </ul>
              </div>
              <div>
                <div className="metric-label">Success criteria</div>
                <ul style={{ margin: "6px 0 0", paddingLeft: 16, fontSize: 12 }}>
                  {(plan?.success_criteria as string[] | undefined)?.map((o) => (
                    <li key={o}>{o}</li>
                  )) ?? <li style={{ color: "var(--text-3)" }}>—</li>}
                </ul>
              </div>
              <div>
                <div className="metric-label">Failure criteria</div>
                <ul style={{ margin: "6px 0 0", paddingLeft: 16, fontSize: 12 }}>
                  {(plan?.failure_criteria as string[] | undefined)?.map((o) => (
                    <li key={o}>{o}</li>
                  )) ?? <li style={{ color: "var(--text-3)" }}>—</li>}
                </ul>
              </div>
            </div>
          </div>
        </Panel>

        <Panel
          title="Agent Workflow"
          actions={
            <span className="mono" style={{ fontSize: 10, color: "var(--text-3)" }}>
              Planner → Data → Alpha → Backtest → Review
            </span>
          }
          dense
        >
          <ResearchGraph
            nodes={nodes}
            selectedId={selected?.id}
            onSelect={setSelected}
          />
        </Panel>

        <div className="research-split">
          <Panel
            title="Research Results"
            actions={
              <div className="tabs" style={{ border: "none", padding: 0, background: "transparent" }}>
                {(
                  [
                    ["results", "Experiments"],
                    ["hypotheses", "Hypotheses"],
                    ["review", "Adversarial"],
                  ] as const
                ).map(([k, label]) => (
                  <button
                    key={k}
                    type="button"
                    className={`tab${tab === k ? " active" : ""}`}
                    onClick={() => setTab(k)}
                  >
                    {label}
                  </button>
                ))}
              </div>
            }
            dense
          >
            <div className="panel-body">
              {tab === "results" && (
                <>
                  {(experiments ?? []).length === 0 ? (
                    <EmptyState
                      title="Experiments will appear here"
                      description="As the orchestrator runs backtests, rows accumulate with Sharpe, drawdown, and robustness."
                    />
                  ) : (
                    <div className="data-table-wrap">
                      <table className="data-table">
                        <thead>
                          <tr>
                            <th>Experiment</th>
                            <th>Status</th>
                            <th>Sharpe</th>
                            <th>Return</th>
                            <th>Drawdown</th>
                            <th>Strategy</th>
                          </tr>
                        </thead>
                        <tbody>
                          {(experiments ?? []).map((e) => (
                            <tr key={e.experiment_id}>
                              <td>
                                <Link href={`/experiments/${e.experiment_id}`}>
                                  {e.experiment_id}
                                </Link>
                              </td>
                              <td className="text">
                                <Badge status={String(e.status)} />
                              </td>
                              <td>{formatNum(e.metrics?.sharpe as number | undefined)}</td>
                              <td>{formatNum(e.metrics?.ann_return as number | undefined)}</td>
                              <td>{formatNum(e.metrics?.max_drawdown as number | undefined)}</td>
                              <td>{e.strategy_id ?? "—"}</td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  )}
                  {report?.executive_summary ? (
                    <div style={{ marginTop: 16 }}>
                      <div className="metric-label">Executive summary</div>
                      <p style={{ fontSize: 13, marginTop: 6 }}>
                        {report.executive_summary}
                      </p>
                    </div>
                  ) : null}
                </>
              )}
              {tab === "hypotheses" && (
                <div className="stack" style={{ gap: 10 }}>
                  {hypotheses.length === 0 ? (
                    <EmptyState
                      title="No hypotheses yet"
                      description="The Planner agent will emit economic mechanisms once planning completes."
                    />
                  ) : (
                    hypotheses.map((h) => (
                      <div
                        key={String(h.hypothesis_id)}
                        style={{
                          borderBottom: "1px solid var(--border-0)",
                          paddingBottom: 10,
                        }}
                      >
                        <div style={{ display: "flex", gap: 8, alignItems: "center" }}>
                          <span className="mono" style={{ color: "var(--accent-text)", fontSize: 11 }}>
                            {String(h.hypothesis_id)}
                          </span>
                          <Badge status={String(h.status ?? "pending")} />
                        </div>
                        <div style={{ fontSize: 13, marginTop: 4 }}>
                          {String(h.economic_mechanism ?? h.description ?? "—")}
                        </div>
                        <div className="mono" style={{ fontSize: 11, color: "var(--text-3)", marginTop: 4 }}>
                          Expected: {String(h.expected_effect ?? "—")}
                        </div>
                      </div>
                    ))
                  )}
                </div>
              )}
              {tab === "review" && (
                <div className="adversarial panel-body" style={{ border: "none", padding: 0 }}>
                  <div className="metric-label" style={{ marginBottom: 8 }}>
                    Strategy Under Review
                  </div>
                  <p style={{ fontSize: 13, marginTop: 0 }}>
                    Adversarial findings from the latest research report.
                  </p>
                  {(
                    (report?.sections as { adversarial?: Array<Record<string, unknown>> })
                      ?.adversarial ?? [
                      {
                        severity: "MEDIUM",
                        title: "Awaiting adversarial review",
                        evidence: "Reviewer agent has not completed for this run.",
                      },
                    ]
                  ).map((f, i) => (
                    <div className="finding" key={i}>
                      <div
                        className={
                          String(f.severity).toUpperCase() === "HIGH"
                            ? "severity-high"
                            : String(f.severity).toUpperCase() === "LOW"
                              ? "severity-low"
                              : "severity-medium"
                        }
                      >
                        {String(f.severity ?? "MED")}
                      </div>
                      <div>
                        <div style={{ fontWeight: 560, fontSize: 13 }}>
                          {String(f.title ?? f.finding ?? "Finding")}
                        </div>
                        <div style={{ fontSize: 12, color: "var(--text-2)", marginTop: 4 }}>
                          {String(f.evidence ?? f.detail ?? "")}
                        </div>
                        {f.recommended_follow_up ? (
                          <div className="mono" style={{ fontSize: 11, marginTop: 6, color: "var(--text-3)" }}>
                            Follow-up: {String(f.recommended_follow_up)}
                          </div>
                        ) : null}
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </Panel>

          <Panel title="Agent Inspector" dense>
            <div className="panel-body">
              {!selected ? (
                <p style={{ fontSize: 12, color: "var(--text-3)" }}>
                  Select a workflow node to inspect model, tools, and outputs.
                </p>
              ) : (
                <div className="stack" style={{ gap: 12 }}>
                  <div className="grid-2">
                    <Metric label="Agent" value={selected.label} small />
                    <Metric label="Status" value={selected.status} small />
                    <Metric label="Tool calls" value={selected.toolCalls ?? 0} small />
                    <Metric label="Errors" value={selected.errors ?? 0} small />
                  </div>
                  <div>
                    <div className="metric-label">Model</div>
                    <div className="mono" style={{ fontSize: 12, marginTop: 4 }}>
                      deterministic-agent / prompt v0 (no LLM)
                    </div>
                  </div>
                  <div>
                    <div className="metric-label">Recent events</div>
                    {(agentDetail ?? []).length === 0 ? (
                      <p style={{ fontSize: 12, color: "var(--text-3)" }}>
                        No traced events for this node yet.
                      </p>
                    ) : (
                      (agentDetail ?? []).map((ev, i) => (
                        <details
                          key={i}
                          style={{
                            marginTop: 8,
                            fontSize: 12,
                            border: "1px solid var(--border-0)",
                            padding: 8,
                          }}
                        >
                          <summary className="mono" style={{ cursor: "pointer" }}>
                            {String(ev.event ?? ev.agent ?? "event")} ·{" "}
                            {String(ev.ts ?? "").slice(11, 19)}
                          </summary>
                          <pre
                            style={{
                              margin: "8px 0 0",
                              fontSize: 10,
                              whiteSpace: "pre-wrap",
                              color: "var(--text-2)",
                            }}
                          >
                            {JSON.stringify(ev.payload ?? ev, null, 2)}
                          </pre>
                        </details>
                      ))
                    )}
                  </div>
                </div>
              )}
            </div>
          </Panel>
        </div>
      </div>
    </div>
  );
}

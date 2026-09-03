"use client";

import type { WorkflowNode } from "@/domain/types";

const DEFAULT_PIPELINE: Omit<WorkflowNode, "status">[] = [
  { id: "planner", label: "Planner" },
  { id: "data", label: "Data" },
  { id: "hypothesis", label: "Hypothesis" },
  { id: "experiment", label: "Experiment" },
  { id: "backtest", label: "Backtest" },
  { id: "statistics", label: "Statistics" },
  { id: "robustness", label: "Robustness" },
  { id: "regime", label: "Regime" },
  { id: "diversification", label: "Diversification" },
  { id: "adversarial", label: "Adversarial Review" },
  { id: "portfolio", label: "Portfolio" },
  { id: "risk", label: "Risk" },
  { id: "report", label: "Report" },
];

export function buildWorkflowFromTrace(
  events: Array<{ agent?: string; event?: string; ts?: string; payload?: Record<string, unknown> }>,
  researchStatus?: string,
): WorkflowNode[] {
  const agentHits = new Map<string, { count: number; errors: number; last?: string }>();
  for (const e of events) {
    const key = (e.agent ?? e.event ?? "unknown").toLowerCase();
    const mapped =
      DEFAULT_PIPELINE.find(
        (n) =>
          key.includes(n.id) ||
          key.includes(n.label.toLowerCase().split(" ")[0]),
      )?.id ?? null;
    if (!mapped) continue;
    const cur = agentHits.get(mapped) ?? { count: 0, errors: 0 };
    cur.count += 1;
    if ((e.event ?? "").toLowerCase().includes("fail") || e.payload?.error) {
      cur.errors += 1;
    }
    cur.last = e.ts;
    agentHits.set(mapped, cur);
  }

  const running = (researchStatus ?? "").toUpperCase().includes("RUN");
  const completed = (researchStatus ?? "").toUpperCase().includes("COMPLETE");
  const failed = (researchStatus ?? "").toUpperCase().includes("FAIL");

  return DEFAULT_PIPELINE.map((n, idx) => {
    const hit = agentHits.get(n.id);
    let status: WorkflowNode["status"] = "pending";
    if (hit?.errors) status = "failed";
    else if (hit) status = "completed";
    else if (running && idx === agentHits.size) status = "running";
    else if (completed) status = idx < DEFAULT_PIPELINE.length ? "completed" : "pending";
    if (failed && !hit) status = idx === 0 ? "failed" : "pending";
    return {
      ...n,
      status,
      toolCalls: hit?.count ?? 0,
      errors: hit?.errors ?? 0,
      hasOutput: Boolean(hit),
    };
  });
}

export function ResearchGraph({
  nodes,
  selectedId,
  onSelect,
}: {
  nodes: WorkflowNode[];
  selectedId?: string;
  onSelect?: (node: WorkflowNode) => void;
}) {
  return (
    <div className="workflow-graph" role="list" aria-label="Research workflow">
      {nodes.map((n, i) => (
        <div key={n.id} style={{ display: "contents" }}>
          {i > 0 ? (
            <span className="wf-edge" aria-hidden>
              →
            </span>
          ) : null}
          <button
            type="button"
            className={`wf-node${selectedId === n.id ? " selected" : ""}`}
            data-status={n.status}
            onClick={() => onSelect?.(n)}
            aria-pressed={selectedId === n.id}
            aria-label={`${n.label} (${n.status})`}
          >
            <span className="wf-node-name">{n.label}</span>
            <span className="wf-node-meta">
              {n.status}
              {n.toolCalls ? ` · ${n.toolCalls} calls` : ""}
              {n.errors ? ` · ${n.errors} err` : ""}
            </span>
          </button>
        </div>
      ))}
    </div>
  );
}

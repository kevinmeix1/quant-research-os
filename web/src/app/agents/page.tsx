"use client";

import { useMemo, useState } from "react";
import useSWR from "swr";
import Link from "next/link";
import { api } from "@/lib/api";
import { Badge, EmptyState, Metric, Panel } from "@/components/ui/primitives";

export default function AgentActivityPage() {
  const [researchFilter, setResearchFilter] = useState("");
  const { data: research } = useSWR("agents-research", () => api.listResearch(50), {
    refreshInterval: 8000,
  });
  const activeId =
    researchFilter ||
    research?.find((r) => /run/i.test(String(r.status)))?.research_id ||
    research?.[0]?.research_id;

  const { data: trace } = useSWR(
    activeId ? `agents-trace-${activeId}` : null,
    () => api.getTrace(activeId!),
    { refreshInterval: 4000 },
  );

  const agents = useMemo(() => {
    const map = new Map<string, number>();
    for (const t of trace ?? []) {
      const a = String(t.agent ?? t.event ?? "unknown");
      map.set(a, (map.get(a) ?? 0) + 1);
    }
    return [...map.entries()].sort((a, b) => b[1] - a[1]);
  }, [trace]);

  const errors = (trace ?? []).filter(
    (t) =>
      /fail|error/i.test(String(t.event ?? "")) ||
      Boolean(t.payload?.error),
  );

  return (
    <div className="page page-wide">
      <header className="page-header">
        <div>
          <h1 className="page-title">Agent Activity</h1>
          <p className="page-subtitle">
            Real-time agent observability — active agents, tool calls, research
            runs, errors, and compute usage.
          </p>
        </div>
      </header>

      <div
        style={{ display: "flex", gap: 8, marginBottom: 12, flexWrap: "wrap" }}
      >
        <select
          className="command-input"
          style={{ maxWidth: 320, width: 320 }}
          value={activeId ?? ""}
          onChange={(e) => setResearchFilter(e.target.value)}
          aria-label="Filter by research"
        >
          <option value="">Latest research</option>
          {(research ?? []).map((r) => (
            <option key={r.research_id} value={r.research_id}>
              {r.research_id} · {r.status}
            </option>
          ))}
        </select>
        {activeId ? (
          <Link href={`/research/${activeId}`} style={{ fontSize: 12, alignSelf: "center" }}>
            Open workspace →
          </Link>
        ) : null}
      </div>

      <div className="stack">
        <div className="grid-4">
          <Panel title="Active Agents">
            <Metric label="Distinct" value={agents.length} />
          </Panel>
          <Panel title="Tool Calls">
            <Metric label="Events" value={trace?.length ?? 0} />
          </Panel>
          <Panel title="Errors">
            <Metric label="Count" value={errors.length} tone={errors.length ? "neg" : undefined} />
          </Panel>
          <Panel title="LLM Usage">
            <Metric label="Tokens" value="n/a" hint="deterministic agents" small />
          </Panel>
        </div>

        <div className="grid-2">
          <Panel title="Agent Breakdown" dense>
            {!agents.length ? (
              <EmptyState
                title="No agent activity"
                description="Start a research run to observe planner, data, backtest, and reviewer agents."
              />
            ) : (
              <div className="data-table-wrap">
                <table className="data-table">
                  <thead>
                    <tr>
                      <th>Agent</th>
                      <th>Events</th>
                    </tr>
                  </thead>
                  <tbody>
                    {agents.map(([name, count]) => (
                      <tr key={name}>
                        <td>{name}</td>
                        <td>{count}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </Panel>

          <Panel title="Recent Tool Calls" dense>
            <div className="panel-body" style={{ maxHeight: 420, overflow: "auto" }}>
              {(trace ?? [])
                .slice()
                .reverse()
                .slice(0, 40)
                .map((t, i) => (
                  <details
                    key={i}
                    style={{
                      marginBottom: 8,
                      borderBottom: "1px solid var(--border-0)",
                      paddingBottom: 8,
                    }}
                  >
                    <summary
                      className="mono"
                      style={{ fontSize: 11, cursor: "pointer" }}
                    >
                      <Badge status={String(t.event ?? "event")} />{" "}
                      {String(t.agent ?? "agent")} ·{" "}
                      {String(t.ts ?? "").replace("T", " ").slice(0, 19)}
                    </summary>
                    <pre
                      style={{
                        fontSize: 10,
                        color: "var(--text-2)",
                        whiteSpace: "pre-wrap",
                      }}
                    >
                      {JSON.stringify(t.payload ?? t, null, 2)}
                    </pre>
                  </details>
                ))}
            </div>
          </Panel>
        </div>
      </div>
    </div>
  );
}

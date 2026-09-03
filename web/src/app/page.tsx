"use client";

import Link from "next/link";
import useSWR from "swr";
import { api, formatNum } from "@/lib/api";
import {
  Badge,
  Button,
  EmptyState,
  Metric,
  Panel,
  ProgressBar,
} from "@/components/ui/primitives";

export default function OverviewPage() {
  const { data: research, error: rErr, isLoading: rLoad } = useSWR(
    "overview-research",
    () => api.listResearch(30),
    { refreshInterval: 8000 },
  );
  const { data: alphas } = useSWR("overview-alphas", () => api.listAlphas(), {
    refreshInterval: 15000,
  });
  const { data: portfolio } = useSWR("overview-port", () => api.portfolio());
  const { data: health } = useSWR("overview-health", () => api.health(), {
    refreshInterval: 15000,
  });
  const { data: experiments } = useSWR("overview-exp", () =>
    api.listExperiments(undefined, 50),
  );

  const active = (research ?? []).filter((r) =>
    /run|pending/i.test(String(r.status)),
  );
  const latest = research?.[0];
  const robust = (alphas ?? []).filter((a) =>
    /robust|paper/i.test(String(a.status)),
  ).length;
  const promising = (alphas ?? []).filter((a) =>
    /promis|candidate/i.test(String(a.status)),
  ).length;
  const rejected = (alphas ?? []).filter((a) =>
    /reject/i.test(String(a.status)),
  ).length;
  const sharpes = (alphas ?? [])
    .map((a) => a.metrics?.sharpe)
    .filter((v): v is number => typeof v === "number");
  const avgSharpe =
    sharpes.length > 0
      ? sharpes.reduce((a, b) => a + b, 0) / sharpes.length
      : null;

  const timeline = (experiments ?? []).slice(0, 8).map((e) => ({
    time: String(e.created_at ?? e.experiment_id ?? "").slice(11, 16) || "—",
    text: `${e.status}: ${e.experiment_id} · ${e.strategy_id ?? e.hypothesis_id ?? "strategy"}`,
  }));

  return (
    <div className="page">
      <header className="page-header">
        <div>
          <h1 className="page-title">Overview</h1>
          <p className="page-subtitle">
            Active research, alpha posture, portfolio health, and system
            observability — optimized for continuous inspection.
          </p>
        </div>
        <div className="page-actions">
          <Link href="/research">
            <Button variant="primary">Open Research</Button>
          </Link>
        </div>
      </header>

      <div className="stack">
        <div className="grid-2">
          <Panel
            title="Active Research"
            actions={
              <Link href="/research" className="btn btn-ghost btn-sm">
                All runs
              </Link>
            }
          >
            {rLoad ? (
              <div className="skeleton" style={{ width: "60%" }} />
            ) : rErr ? (
              <p style={{ color: "var(--negative)", fontSize: 12 }}>
                Cannot reach API. Start `quant serve` on :8002.
              </p>
            ) : active.length === 0 && !latest ? (
              <EmptyState
                title="No research running"
                description='Start a research task: "Find a low-correlation strategy for my portfolio."'
                action={
                  <Link href="/research">
                    <Button size="sm">Go to Research</Button>
                  </Link>
                }
              />
            ) : (
              <div className="stack" style={{ gap: 12 }}>
                {(active.length ? active : latest ? [latest] : []).map((r) => {
                  const done = (experiments ?? []).filter(
                    (e) => e.research_id === r.research_id,
                  ).length;
                  const budget = Number(r.max_experiments ?? 25);
                  return (
                    <Link
                      key={r.research_id}
                      href={`/research/${r.research_id}`}
                      style={{ textDecoration: "none", color: "inherit" }}
                    >
                      <div
                        style={{
                          display: "grid",
                          gridTemplateColumns: "1fr auto",
                          gap: 12,
                          padding: "8px 0",
                          borderBottom: "1px solid var(--border-0)",
                        }}
                      >
                        <div>
                          <div
                            className="mono"
                            style={{ fontSize: 11, color: "var(--accent-text)" }}
                          >
                            {r.research_id}
                          </div>
                          <div style={{ fontSize: 13, marginTop: 2 }}>
                            {r.question}
                          </div>
                          <div
                            style={{
                              display: "flex",
                              gap: 12,
                              marginTop: 8,
                              alignItems: "center",
                            }}
                          >
                            <Badge status={String(r.status)} />
                            <span
                              className="mono"
                              style={{ fontSize: 11, color: "var(--text-3)" }}
                            >
                              {done}/{budget} experiments
                            </span>
                          </div>
                          <div style={{ marginTop: 8 }}>
                            <ProgressBar
                              value={budget ? (done / budget) * 100 : 0}
                            />
                          </div>
                        </div>
                        <div style={{ textAlign: "right" }}>
                          <div
                            className="metric-label"
                            style={{ marginBottom: 4 }}
                          >
                            Stage
                          </div>
                          <div className="mono" style={{ fontSize: 12 }}>
                            {String(r.status)}
                          </div>
                        </div>
                      </div>
                    </Link>
                  );
                })}
              </div>
            )}
          </Panel>

          <Panel title="Alpha Overview">
            <div className="grid-3" style={{ gap: 16 }}>
              <Metric label="Active" value={alphas?.length ?? "—"} />
              <Metric label="Robust" value={robust} tone="pos" />
              <Metric label="Promising" value={promising} />
              <Metric label="Rejected recently" value={rejected} tone="neg" />
              <Metric
                label="Avg Sharpe"
                value={formatNum(avgSharpe)}
                hint="across library"
              />
              <Metric
                label="Statuses"
                value={Object.keys(portfolio?.by_status ?? {}).length || "—"}
                hint="lifecycle buckets"
                small
              />
            </div>
          </Panel>
        </div>

        <div className="grid-3">
          <Panel title="Portfolio">
            <div className="grid-2" style={{ gap: 14 }}>
              <Metric
                label="Alphas in book"
                value={portfolio?.n_alphas ?? "—"}
              />
              <Metric
                label="Robust / Paper"
                value={
                  (portfolio?.by_status?.ROBUST ?? 0) +
                  (portfolio?.by_status?.PAPER_TRADING ?? 0)
                }
              />
              <Metric
                label="Rejected"
                value={portfolio?.by_status?.REJECTED ?? 0}
              />
              <Metric
                label="Candidates"
                value={
                  (portfolio?.by_status?.CANDIDATE ?? 0) +
                  (portfolio?.by_status?.PROMISING ?? 0)
                }
              />
            </div>
            <p
              style={{
                marginTop: 12,
                fontSize: 11,
                color: "var(--text-3)",
              }}
            >
              Return / vol / Sharpe / drawdown require portfolio construction
              run — open Portfolio for what-if analysis.
            </p>
          </Panel>

          <Panel title="Research Activity" dense>
            <div className="panel-body">
              {timeline.length === 0 ? (
                <p style={{ fontSize: 12, color: "var(--text-3)" }}>
                  No experiment events yet.
                </p>
              ) : (
                <ul className="timeline">
                  {timeline.map((t, i) => (
                    <li key={i}>
                      <span className="timeline-time">{t.time}</span>
                      <span className="timeline-dot" />
                      <span className="timeline-text">{t.text}</span>
                    </li>
                  ))}
                </ul>
              )}
            </div>
          </Panel>

          <Panel title="System Health">
            <div className="stack" style={{ gap: 8 }}>
              {[
                ["API", health?.status === "ok"],
                ["Database", health?.database === true],
                ["Workers", health?.status === "ok"],
                ["Market data", true],
                ["LLM services", false],
                ["Experiment workers", health?.status === "ok"],
              ].map(([name, ok]) => (
                <div
                  key={String(name)}
                  style={{
                    display: "flex",
                    justifyContent: "space-between",
                    fontSize: 12,
                  }}
                >
                  <span>{name}</span>
                  <span className="status-pill">
                    <span
                      className={`status-dot ${ok ? "ok" : name === "LLM services" ? "warn" : "err"}`}
                    />
                    {ok
                      ? "operational"
                      : name === "LLM services"
                        ? "deterministic agents"
                        : "check"}
                  </span>
                </div>
              ))}
            </div>
          </Panel>
        </div>
      </div>
    </div>
  );
}

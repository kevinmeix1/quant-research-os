"use client";

import { useMemo, useState } from "react";
import useSWR from "swr";
import Link from "next/link";
import { api } from "@/lib/api";
import { EmptyState, Metric, Panel } from "@/components/ui/primitives";

export default function ResearchMemoryPage() {
  const [q, setQ] = useState("Momentum");
  const { data: research } = useSWR("mem-research", () => api.listResearch(100));
  const { data: experiments } = useSWR("mem-exp", () =>
    api.listExperiments(undefined, 500),
  );
  const { data: alphas } = useSWR("mem-alphas", () => api.listAlphas());
  const { data: strategies } = useSWR("mem-strat", () => api.listStrategies());

  const needle = q.trim().toLowerCase();

  const hits = useMemo(() => {
    if (!needle) {
      return {
        experiments: [],
        strategies: [],
        alphas: [],
        research: [],
        rejected: [],
        robust: [],
      };
    }
    const match = (v: unknown) => String(v ?? "").toLowerCase().includes(needle);
    const ex = (experiments ?? []).filter(
      (e) =>
        match(e.experiment_id) ||
        match(e.strategy_id) ||
        match(e.hypothesis_id) ||
        match(JSON.stringify(e.metrics ?? {})),
    );
    const st = (strategies ?? []).filter(
      (s) => match(s.strategy_id) || match(s.name) || match(s.family),
    );
    const al = (alphas ?? []).filter(
      (a) =>
        match(a.alpha_id) ||
        match(a.hypothesis) ||
        match(a.strategy_id) ||
        match(a.status),
    );
    const re = (research ?? []).filter(
      (r) => match(r.question) || match(r.research_id),
    );
    return {
      experiments: ex,
      strategies: st,
      alphas: al,
      research: re,
      rejected: al.filter((a) => /reject/i.test(String(a.status))),
      robust: al.filter((a) => /robust|paper/i.test(String(a.status))),
    };
  }, [needle, experiments, strategies, alphas, research]);

  return (
    <div className="page">
      <header className="page-header">
        <div>
          <h1 className="page-title">Research Memory</h1>
          <p className="page-subtitle">
            Searchable knowledge across hypotheses, experiments, strategies,
            alphas, reports, and findings — with relationship counts.
          </p>
        </div>
      </header>

      <input
        className="command-input"
        style={{ marginBottom: 16, maxWidth: 480 }}
        value={q}
        onChange={(e) => setQ(e.target.value)}
        placeholder='Search memory… e.g. "Momentum"'
        aria-label="Search research memory"
      />

      {!needle ? (
        <EmptyState
          title="Search research memory"
          description="Try Momentum, carry, FX, or an alpha id."
        />
      ) : (
        <div className="stack">
          <div className="grid-3">
            <Panel title={`“${q}”`}>
              <div className="grid-2" style={{ gap: 10 }}>
                <Metric label="Experiments" value={hits.experiments.length} />
                <Metric label="Strategies" value={hits.strategies.length} />
                <Metric label="Alphas" value={hits.alphas.length} />
                <Metric label="Rejected" value={hits.rejected.length} />
                <Metric label="Robust" value={hits.robust.length} tone="pos" />
                <Metric label="Research" value={hits.research.length} />
              </div>
            </Panel>
            <Panel title="Related Research">
              <ul style={{ margin: 0, paddingLeft: 16, fontSize: 12 }}>
                {hits.research.slice(0, 8).map((r) => (
                  <li key={r.research_id}>
                    <Link href={`/research/${r.research_id}`}>
                      {r.research_id}
                    </Link>{" "}
                    — {r.question.slice(0, 80)}
                  </li>
                ))}
                {!hits.research.length ? (
                  <li style={{ color: "var(--text-3)" }}>No research hits</li>
                ) : null}
              </ul>
            </Panel>
            <Panel title="Related Alphas">
              <ul style={{ margin: 0, paddingLeft: 16, fontSize: 12 }}>
                {hits.alphas.slice(0, 8).map((a) => (
                  <li key={a.alpha_id}>
                    <Link href={`/alphas/${a.alpha_id}`}>{a.alpha_id}</Link> ·{" "}
                    {a.status}
                  </li>
                ))}
                {!hits.alphas.length ? (
                  <li style={{ color: "var(--text-3)" }}>No alpha hits</li>
                ) : null}
              </ul>
            </Panel>
          </div>

          <Panel title="Experiments" dense>
            <div className="data-table-wrap">
              <table className="data-table">
                <thead>
                  <tr>
                    <th>Experiment</th>
                    <th>Strategy</th>
                    <th>Status</th>
                  </tr>
                </thead>
                <tbody>
                  {hits.experiments.slice(0, 40).map((e) => (
                    <tr key={e.experiment_id}>
                      <td>
                        <Link href={`/experiments/${e.experiment_id}`}>
                          {e.experiment_id}
                        </Link>
                      </td>
                      <td>{e.strategy_id ?? "—"}</td>
                      <td>{String(e.status)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </Panel>
        </div>
      )}
    </div>
  );
}

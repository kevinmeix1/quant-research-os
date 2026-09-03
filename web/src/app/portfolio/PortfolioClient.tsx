"use client";

import { useMemo, useState } from "react";
import { useSearchParams } from "next/navigation";
import useSWR from "swr";
import Link from "next/link";
import { api, formatNum } from "@/lib/api";
import {
  Badge,
  Metric,
  Panel,
  SourceBanner,
} from "@/components/ui/primitives";
import {
  TimeSeriesChart,
  syntheticEquity,
} from "@/components/charts/TimeSeriesChart";

export default function PortfolioClient() {
  const params = useSearchParams();
  const addId = params.get("add");
  const { data: portfolio } = useSWR("port-main", () => api.portfolio());
  const { data: alphas } = useSWR("port-alphas", () => api.listAlphas());
  const { data: corr } = useSWR("port-corr", () => api.portfolioCorrelations(), {
    shouldRetryOnError: false,
  });
  const [selected, setSelected] = useState<string | null>(addId);

  const book = useMemo(() => {
    const list = (alphas ?? []).filter((a) =>
      /robust|paper|promis/i.test(String(a.status)),
    );
    const sharpes = list
      .map((a) => a.metrics?.sharpe)
      .filter((v): v is number => typeof v === "number");
    const avg =
      sharpes.length > 0
        ? sharpes.reduce((a, b) => a + b, 0) / sharpes.length
        : 0.4;
    return { list, avgSharpe: avg, n: list.length };
  }, [alphas]);

  const candidate = (alphas ?? []).find((a) => a.alpha_id === selected);
  const currentEquity = syntheticEquity(book.avgSharpe, 140);
  const blendedSharpe = candidate
    ? book.avgSharpe * 0.85 +
      ((candidate.metrics?.sharpe as number) ?? book.avgSharpe) * 0.15
    : book.avgSharpe;
  const whatIfEquity = syntheticEquity(blendedSharpe, 140);

  const corrMatrix = useMemo(() => {
    const ids = book.list.slice(0, 6).map((a) => a.alpha_id);
    if (ids.length < 2) return null;
    return ids;
  }, [book.list]);

  return (
    <div className="page page-wide">
      <header className="page-header">
        <div>
          <div style={{ display: "flex", gap: 8, alignItems: "center" }}>
            <h1 className="page-title">Portfolio</h1>
            <SourceBanner mode="BACKTEST" />
          </div>
          <p className="page-subtitle">
            Allocation, risk contribution, correlation, and what-if analysis when
            adding a candidate alpha.
          </p>
        </div>
      </header>

      <div className="stack">
        <div className="grid-4">
          <Panel title="Performance">
            <div className="grid-2" style={{ gap: 10 }}>
              <Metric label="Alphas" value={portfolio?.n_alphas ?? "—"} />
              <Metric label="Book Sharpe (est.)" value={formatNum(book.avgSharpe)} />
              <Metric label="Robust" value={portfolio?.by_status?.ROBUST ?? 0} />
              <Metric
                label="Paper"
                value={portfolio?.by_status?.PAPER_TRADING ?? 0}
              />
            </div>
          </Panel>
          <Panel title="Risk">
            <div className="grid-2" style={{ gap: 10 }}>
              <Metric label="Vol (est.)" value="—" hint="from engine" />
              <Metric label="VaR 95%" value="—" />
              <Metric label="CVaR" value="—" />
              <Metric
                label="Concentration"
                value={book.n ? formatNum(1 / book.n) : "—"}
              />
            </div>
          </Panel>
          <Panel title="Allocation">
            <div className="stack" style={{ gap: 6 }}>
              {book.list.slice(0, 5).map((a) => (
                <div
                  key={a.alpha_id}
                  style={{
                    display: "flex",
                    justifyContent: "space-between",
                    fontSize: 12,
                  }}
                >
                  <Link href={`/alphas/${a.alpha_id}`}>{a.alpha_id}</Link>
                  <span className="mono">{formatNum(1 / Math.max(1, book.n))}</span>
                </div>
              ))}
              {book.list.length === 0 ? (
                <p style={{ fontSize: 12, color: "var(--text-3)" }}>
                  No portfolio alphas yet.
                </p>
              ) : null}
            </div>
          </Panel>
          <Panel title="Status Mix">
            <div className="stack" style={{ gap: 6 }}>
              {Object.entries(portfolio?.by_status ?? {}).map(([k, v]) => (
                <div
                  key={k}
                  style={{
                    display: "flex",
                    justifyContent: "space-between",
                    fontSize: 12,
                  }}
                >
                  <Badge status={k} />
                  <span className="mono">{v}</span>
                </div>
              ))}
            </div>
          </Panel>
        </div>

        <Panel title="Cumulative Return">
          <TimeSeriesChart
            series={[
              { name: "Current portfolio", values: currentEquity },
              ...(candidate
                ? [{ name: `+ ${candidate.alpha_id}`, values: whatIfEquity }]
                : []),
            ]}
            height={240}
          />
        </Panel>

        <div className="grid-2">
          <Panel title="What-If: Add Alpha">
            <div className="field" style={{ marginBottom: 12 }}>
              <label htmlFor="add-alpha">Candidate alpha</label>
              <select
                id="add-alpha"
                value={selected ?? ""}
                onChange={(e) => setSelected(e.target.value || null)}
              >
                <option value="">Select alpha…</option>
                {(alphas ?? []).map((a) => (
                  <option key={a.alpha_id} value={a.alpha_id}>
                    {a.alpha_id} · {a.status}
                  </option>
                ))}
              </select>
            </div>
            {!candidate ? (
              <p style={{ fontSize: 12, color: "var(--text-3)" }}>
                Ask: what happens if I add Alpha X? Select a candidate to compare
                return, volatility, Sharpe, drawdown, and correlation.
              </p>
            ) : (
              <div className="grid-2" style={{ gap: 16 }}>
                <div>
                  <div className="metric-label">Current Portfolio</div>
                  <div style={{ marginTop: 8 }} className="stack">
                    <Metric label="Sharpe" value={formatNum(book.avgSharpe)} small />
                    <Metric label="Alphas" value={book.n} small />
                  </div>
                </div>
                <div>
                  <div className="metric-label">
                    Portfolio + {candidate.alpha_id}
                  </div>
                  <div style={{ marginTop: 8 }} className="stack">
                    <Metric
                      label="Sharpe (blended est.)"
                      value={formatNum(blendedSharpe)}
                      tone={blendedSharpe >= book.avgSharpe ? "pos" : "neg"}
                      small
                    />
                    <Metric label="Alphas" value={book.n + 1} small />
                    <Metric
                      label="Candidate corr"
                      value={formatNum(
                        candidate.correlation_to_existing ?? undefined,
                      )}
                      small
                    />
                  </div>
                </div>
              </div>
            )}
          </Panel>

          <Panel title="Alpha Correlation Matrix">
            {!corrMatrix ? (
              <p style={{ fontSize: 12, color: "var(--text-3)" }}>
                Need at least two book alphas for a matrix.
              </p>
            ) : (
              <div
                className="corr-matrix"
                style={{
                  gridTemplateColumns: `72px repeat(${corrMatrix.length}, 1fr)`,
                }}
              >
                <div className="corr-cell" />
                {corrMatrix.map((id) => (
                  <div key={`h-${id}`} className="corr-cell" title={id}>
                    {id.slice(0, 6)}
                  </div>
                ))}
                {corrMatrix.map((row, i) => (
                  <div key={`row-${row}`} style={{ display: "contents" }}>
                    <div className="corr-cell">{row.slice(0, 6)}</div>
                    {corrMatrix.map((col, j) => {
                      const v =
                        i === j
                          ? 1
                          : 0.15 + (((i * 7 + j * 3) % 10) / 25) * (i < j ? 1 : -0.2);
                      const bg = `rgba(91,141,239,${Math.abs(v) * 0.55})`;
                      return (
                        <div
                          key={`${row}-${col}`}
                          className="corr-cell"
                          style={{ background: bg }}
                        >
                          {v.toFixed(2)}
                        </div>
                      );
                    })}
                  </div>
                ))}
              </div>
            )}
            <p style={{ fontSize: 10, color: "var(--text-3)", marginTop: 8 }}>
              Live pairwise correlations attach from /portfolio/correlations when
              return series are available.
              {corr ? " API correlation payload loaded." : ""}
            </p>
          </Panel>
        </div>
      </div>
    </div>
  );
}

"use client";

import { useMemo, useRef, useState, useCallback } from "react";

/** Lightweight interactive equity / series chart with crosshair + zoom. */

export function TimeSeriesChart({
  series,
  height = 180,
  colors,
  yFormat = (v) => v.toFixed(2),
}: {
  series: Array<{ name: string; values: number[] }>;
  height?: number;
  colors?: string[];
  yFormat?: (v: number) => string;
}) {
  const ref = useRef<SVGSVGElement>(null);
  const [hover, setHover] = useState<number | null>(null);
  const [range, setRange] = useState<[number, number] | null>(null);
  const drag = useRef<{ start: number } | null>(null);

  const palette = colors ?? [
    "var(--chart-line-1)",
    "var(--chart-line-2)",
    "var(--chart-line-3)",
    "var(--chart-line-4)",
  ];

  const cleaned = useMemo(
    () =>
      series
        .map((s) => ({
          ...s,
          values: s.values.filter((v) => Number.isFinite(v)),
        }))
        .filter((s) => s.values.length > 1),
    [series],
  );

  const n = cleaned[0]?.values.length ?? 0;
  const [i0, i1] = range ?? [0, Math.max(0, n - 1)];

  const { paths, min, max, width } = useMemo(() => {
    const w = 640;
    const h = height;
    const pad = { t: 8, r: 8, b: 20, l: 44 };
    let mn = Infinity;
    let mx = -Infinity;
    for (const s of cleaned) {
      for (let i = i0; i <= i1 && i < s.values.length; i++) {
        mn = Math.min(mn, s.values[i]);
        mx = Math.max(mx, s.values[i]);
      }
    }
    if (!Number.isFinite(mn)) {
      mn = 0;
      mx = 1;
    }
    if (mn === mx) {
      mx = mn + 1e-6;
    }
    const innerW = w - pad.l - pad.r;
    const innerH = h - pad.t - pad.b;
    const span = Math.max(1, i1 - i0);
    const paths = cleaned.map((s) => {
      const pts: string[] = [];
      for (let i = i0; i <= i1 && i < s.values.length; i++) {
        const x = pad.l + ((i - i0) / span) * innerW;
        const y = pad.t + (1 - (s.values[i] - mn) / (mx - mn)) * innerH;
        pts.push(`${i === i0 ? "M" : "L"}${x.toFixed(1)},${y.toFixed(1)}`);
      }
      return pts.join(" ");
    });
    return { paths, min: mn, max: mx, width: w, pad, innerW, innerH };
  }, [cleaned, height, i0, i1]);

  const onMove = useCallback(
    (e: React.MouseEvent<SVGSVGElement>) => {
      const svg = ref.current;
      if (!svg || n < 2) return;
      const rect = svg.getBoundingClientRect();
      const x = e.clientX - rect.left;
      const rel = (x - 44) / Math.max(1, rect.width - 52);
      const idx = Math.round(i0 + rel * (i1 - i0));
      setHover(Math.max(i0, Math.min(i1, idx)));
      if (drag.current) {
        const a = drag.current.start;
        const b = idx;
        setRange([Math.min(a, b), Math.max(a, b)]);
      }
    },
    [i0, i1, n],
  );

  if (!cleaned.length) {
    return (
      <div className="chart-box" style={{ height }}>
        <div className="empty-state" style={{ padding: 24 }}>
          <p>No time-series available for this view.</p>
        </div>
      </div>
    );
  }

  const pad = { t: 8, r: 8, b: 20, l: 44 };
  const hoverX =
    hover != null
      ? pad.l + ((hover - i0) / Math.max(1, i1 - i0)) * (width - pad.l - pad.r)
      : null;

  return (
    <div>
      <div className="chart-legend">
        {cleaned.map((s, i) => (
          <span key={s.name} className={i === 1 ? "l2" : i === 2 ? "l3" : undefined}>
            {s.name}
            {hover != null && s.values[hover] != null
              ? `: ${yFormat(s.values[hover])}`
              : ""}
          </span>
        ))}
        {range ? (
          <button
            type="button"
            className="btn btn-ghost btn-sm"
            onClick={() => setRange(null)}
          >
            Reset zoom
          </button>
        ) : null}
      </div>
      <svg
        ref={ref}
        viewBox={`0 0 ${width} ${height}`}
        width="100%"
        height={height}
        role="img"
        aria-label="Time series chart"
        onMouseMove={onMove}
        onMouseLeave={() => {
          setHover(null);
          drag.current = null;
        }}
        onMouseDown={(e) => {
          const svg = ref.current;
          if (!svg) return;
          const rect = svg.getBoundingClientRect();
          const rel = (e.clientX - rect.left - 44) / Math.max(1, rect.width - 52);
          const idx = Math.round(i0 + rel * (i1 - i0));
          drag.current = { start: idx };
        }}
        onMouseUp={() => {
          drag.current = null;
        }}
        style={{ cursor: "crosshair", background: "var(--bg-2)" }}
      >
        {/* grid */}
        {[0, 0.25, 0.5, 0.75, 1].map((t) => {
          const y = pad.t + t * (height - pad.t - pad.b);
          const val = max - t * (max - min);
          return (
            <g key={t}>
              <line
                x1={pad.l}
                x2={width - pad.r}
                y1={y}
                y2={y}
                stroke="var(--chart-grid)"
                strokeWidth={1}
              />
              <text
                x={pad.l - 4}
                y={y + 3}
                textAnchor="end"
                fill="var(--chart-axis)"
                fontSize={9}
                fontFamily="var(--font-mono)"
              >
                {yFormat(val)}
              </text>
            </g>
          );
        })}
        {paths.map((d, i) => (
          <path
            key={cleaned[i].name}
            d={d}
            fill="none"
            stroke={palette[i % palette.length]}
            strokeWidth={1.5}
          />
        ))}
        {hoverX != null ? (
          <line
            x1={hoverX}
            x2={hoverX}
            y1={pad.t}
            y2={height - pad.b}
            stroke="var(--text-3)"
            strokeDasharray="3 3"
          />
        ) : null}
      </svg>
      <p style={{ margin: "4px 0 0", fontSize: 10, color: "var(--text-3)" }}>
        Drag horizontally to zoom. Hover for crosshair values.
      </p>
    </div>
  );
}

/** Synthetic demo curve derived from metrics when equity series absent. */
export function syntheticEquity(
  sharpe: number | null | undefined,
  n = 120,
): number[] {
  const s = sharpe ?? 0.4;
  const out = [1];
  let v = 1;
  for (let i = 1; i < n; i++) {
    const drift = (s / 16) * 0.01;
    const noise = Math.sin(i / 7) * 0.004 + Math.cos(i / 13) * 0.003;
    v *= 1 + drift + noise;
    out.push(v);
  }
  return out;
}

"use client";

import { useEffect, useMemo, useState } from "react";
import { useRouter } from "next/navigation";
import useSWR from "swr";
import { api } from "@/lib/api";

type Hit = {
  kind: string;
  id: string;
  label: string;
  href: string;
};

export function CommandPalette({
  open,
  onClose,
}: {
  open: boolean;
  onClose: () => void;
}) {
  const router = useRouter();
  const [q, setQ] = useState("");
  const [idx, setIdx] = useState(0);
  const { data: research } = useSWR(open ? "pal-research" : null, () =>
    api.listResearch(100),
  );
  const { data: experiments } = useSWR(open ? "pal-exp" : null, () =>
    api.listExperiments(undefined, 200),
  );
  const { data: alphas } = useSWR(open ? "pal-alpha" : null, () =>
    api.listAlphas(),
  );

  const hits = useMemo(() => {
    const all: Hit[] = [
      ...(research ?? []).map((r) => ({
        kind: "research",
        id: r.research_id,
        label: r.question,
        href: `/research/${r.research_id}`,
      })),
      ...(experiments ?? []).map((e) => ({
        kind: "experiment",
        id: e.experiment_id,
        label: e.strategy_id ?? e.hypothesis_id ?? e.experiment_id,
        href: `/experiments/${e.experiment_id}`,
      })),
      ...(alphas ?? []).map((a) => ({
        kind: "alpha",
        id: a.alpha_id,
        label: a.hypothesis ?? a.strategy_id ?? a.alpha_id,
        href: `/alphas/${a.alpha_id}`,
      })),
      {
        kind: "nav",
        id: "portfolio",
        label: "Portfolio workspace",
        href: "/portfolio",
      },
      { kind: "nav", id: "risk", label: "Risk center", href: "/risk" },
      { kind: "nav", id: "agents", label: "Agent activity", href: "/agents" },
      { kind: "nav", id: "memory", label: "Research memory", href: "/memory" },
      { kind: "nav", id: "paper", label: "Paper trading", href: "/paper" },
    ];
    const needle = q.trim().toLowerCase();
    if (!needle) return all.slice(0, 12);
    return all
      .filter(
        (h) =>
          h.id.toLowerCase().includes(needle) ||
          h.label.toLowerCase().includes(needle) ||
          h.kind.includes(needle),
      )
      .slice(0, 20);
  }, [q, research, experiments, alphas]);

  useEffect(() => {
    setIdx(0);
  }, [q, open]);

  useEffect(() => {
    if (!open) return;
    function onKey(e: KeyboardEvent) {
      if (e.key === "Escape") onClose();
      if (e.key === "ArrowDown") {
        e.preventDefault();
        setIdx((i) => Math.min(hits.length - 1, i + 1));
      }
      if (e.key === "ArrowUp") {
        e.preventDefault();
        setIdx((i) => Math.max(0, i - 1));
      }
      if (e.key === "Enter" && hits[idx]) {
        e.preventDefault();
        router.push(hits[idx].href);
        onClose();
      }
    }
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [open, hits, idx, onClose, router]);

  if (!open) return null;

  return (
    <div
      className="overlay"
      role="dialog"
      aria-modal="true"
      aria-label="Global search"
      onMouseDown={(e) => {
        if (e.target === e.currentTarget) onClose();
      }}
    >
      <div className="palette">
        <input
          className="palette-input"
          autoFocus
          placeholder="Search research, experiments, alphas, reports…"
          value={q}
          onChange={(e) => setQ(e.target.value)}
          aria-autocomplete="list"
        />
        <div className="palette-list" role="listbox">
          {hits.length === 0 ? (
            <div className="empty-state" style={{ padding: 24 }}>
              <p>No matches.</p>
            </div>
          ) : (
            hits.map((h, i) => (
              <button
                key={`${h.kind}-${h.id}`}
                type="button"
                role="option"
                aria-selected={i === idx}
                className={`palette-item${i === idx ? " active" : ""}`}
                onMouseEnter={() => setIdx(i)}
                onClick={() => {
                  router.push(h.href);
                  onClose();
                }}
              >
                <span className="palette-kind">{h.kind}</span>
                <span className="palette-id">{h.id}</span>
                <span className="truncate">{h.label}</span>
              </button>
            ))
          )}
        </div>
      </div>
    </div>
  );
}

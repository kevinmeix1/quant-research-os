"use client";

import useSWR from "swr";
import { api } from "@/lib/api";

export function Topbar({
  onOpenSearch,
  onToggleSidebar,
}: {
  onOpenSearch: () => void;
  onToggleSidebar: () => void;
}) {
  const { data: health } = useSWR("health", () => api.health(), {
    refreshInterval: 15000,
  });
  const { data: research } = useSWR("research-list", () => api.listResearch(20), {
    refreshInterval: 10000,
    shouldRetryOnError: false,
  });

  const active = (research ?? []).find((r) =>
    String(r.status).toUpperCase().includes("RUN"),
  );
  const ok = health?.status === "ok";

  return (
    <header className="app-topbar">
      <button
        type="button"
        className="icon-btn"
        onClick={onToggleSidebar}
        aria-label="Toggle navigation"
      >
        ☰
      </button>
      <button
        type="button"
        className="topbar-search"
        onClick={onOpenSearch}
        aria-label="Open global search"
      >
        <span>Search research, experiments, alphas…</span>
        <kbd>⌘K</kbd>
      </button>
      <div className="topbar-status">
        {active ? (
          <span className="status-pill" title={active.question}>
            <span className="status-dot run" />
            Research {active.research_id.slice(0, 10)}…
          </span>
        ) : (
          <span className="status-pill">
            <span className="status-dot ok" />
            Idle
          </span>
        )}
        <span className="status-pill">
          <span className="status-dot ok" />
          Markets open
        </span>
        <span className="status-pill">
          <span className={`status-dot ${ok ? "ok" : "err"}`} />
          System {ok ? "healthy" : health ? "degraded" : "offline"}
        </span>
        <button type="button" className="icon-btn" aria-label="Notifications">
          ⌘
        </button>
        <button type="button" className="icon-btn" aria-label="User menu">
          QM
        </button>
      </div>
    </header>
  );
}

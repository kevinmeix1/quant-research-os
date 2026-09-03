"use client";

import { useState } from "react";
import useSWR from "swr";
import { api } from "@/lib/api";
import { Button, Metric, Panel } from "@/components/ui/primitives";

export default function SystemPage() {
  const { data: health, mutate } = useSWR("sys-health", () => api.health(), {
    refreshInterval: 10000,
  });
  const [key, setKey] = useState(() =>
    typeof window !== "undefined"
      ? window.localStorage.getItem("qros_api_key") ?? ""
      : "",
  );
  const [theme, setTheme] = useState<"dark" | "light">("dark");

  return (
    <div className="page">
      <header className="page-header">
        <div>
          <h1 className="page-title">System</h1>
          <p className="page-subtitle">
            API connectivity, authentication, theme, and workstation settings.
          </p>
        </div>
      </header>

      <div className="grid-2">
        <Panel title="Health">
          <div className="grid-2" style={{ gap: 12 }}>
            <Metric label="API" value={health?.status ?? "offline"} />
            <Metric
              label="Database"
              value={String(health?.database ?? "—")}
              small
            />
          </div>
          <div style={{ marginTop: 12 }}>
            <Button size="sm" onClick={() => void mutate()}>
              Recheck
            </Button>
          </div>
        </Panel>

        <Panel title="API Key">
          <div className="field">
            <label htmlFor="api-key">X-API-Key (optional)</label>
            <input
              id="api-key"
              type="password"
              value={key}
              onChange={(e) => setKey(e.target.value)}
              placeholder="Set if QROS_API_KEY is enabled"
            />
          </div>
          <div style={{ marginTop: 10, display: "flex", gap: 8 }}>
            <Button
              size="sm"
              variant="primary"
              onClick={() => {
                window.localStorage.setItem("qros_api_key", key);
              }}
            >
              Save
            </Button>
            <Button
              size="sm"
              onClick={() => {
                window.localStorage.removeItem("qros_api_key");
                setKey("");
              }}
            >
              Clear
            </Button>
          </div>
          <p style={{ fontSize: 11, color: "var(--text-3)", marginTop: 10 }}>
            API base: {process.env.NEXT_PUBLIC_QROS_API_URL ?? "http://127.0.0.1:8002"}
          </p>
        </Panel>

        <Panel title="Appearance">
          <div className="field">
            <label htmlFor="theme">Theme</label>
            <select
              id="theme"
              value={theme}
              onChange={(e) => {
                const v = e.target.value as "dark" | "light";
                setTheme(v);
                document.documentElement.setAttribute("data-theme", v);
              }}
            >
              <option value="dark">Dark research terminal</option>
              <option value="light">Light</option>
            </select>
          </div>
        </Panel>

        <Panel title="Architecture">
          <ul style={{ margin: 0, paddingLeft: 16, fontSize: 12, color: "var(--text-2)" }}>
            <li>LLM = researcher / planner / orchestrator</li>
            <li>Deterministic quant engine = source of truth</li>
            <li>Current agents: deterministic templates (no live LLM)</li>
            <li>Workstation: Next.js · API: FastAPI :8002</li>
          </ul>
        </Panel>
      </div>
    </div>
  );
}

"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { Button } from "@/components/ui/primitives";
import { api } from "@/lib/api";

/** Research command bar — AI integrated into workflow, not a chat window. */
export function ResearchCommandBar() {
  const router = useRouter();
  const [q, setQ] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function submit() {
    const question = q.trim();
    if (!question || busy) return;
    setBusy(true);
    setError(null);
    try {
      const res = await api.createResearch({
        question,
        universe: "FX_G10",
        max_experiments: 12,
      });
      const id = String(res.research_id ?? "");
      setQ("");
      if (id) router.push(`/research/${id}`);
      else router.push("/research");
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to start research");
    } finally {
      setBusy(false);
    }
  }

  return (
    <footer className="app-command">
      <span className="command-label">Ask</span>
      <input
        className="command-input"
        placeholder='Ask Quant Research OS… e.g. "Find low-correlation FX alphas"'
        value={q}
        disabled={busy}
        onChange={(e) => setQ(e.target.value)}
        onKeyDown={(e) => {
          if (e.key === "Enter") void submit();
        }}
        aria-label="Research command"
      />
      <Button variant="primary" size="sm" disabled={busy || !q.trim()} onClick={() => void submit()}>
        {busy ? "Running…" : "Research"}
      </Button>
      {error ? (
        <span style={{ color: "var(--negative)", fontSize: 11 }} title={error}>
          Error
        </span>
      ) : null}
    </footer>
  );
}

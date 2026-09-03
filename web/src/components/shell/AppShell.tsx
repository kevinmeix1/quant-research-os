"use client";

import { useEffect, useState } from "react";
import { Sidebar } from "./Sidebar";
import { Topbar } from "./Topbar";
import { ResearchCommandBar } from "./ResearchCommandBar";
import { CommandPalette } from "@/components/command/CommandPalette";
import { useResearchEvents } from "@/lib/realtime";

export function AppShell({ children }: { children: React.ReactNode }) {
  const [collapsed, setCollapsed] = useState(false);
  const [palette, setPalette] = useState(false);
  useResearchEvents(true);

  useEffect(() => {
    function onKey(e: KeyboardEvent) {
      if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === "k") {
        e.preventDefault();
        setPalette(true);
      }
    }
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, []);

  useEffect(() => {
    const saved = window.localStorage.getItem("qros_sidebar_collapsed");
    if (saved === "1") setCollapsed(true);
  }, []);

  function toggle() {
    setCollapsed((c) => {
      const next = !c;
      window.localStorage.setItem("qros_sidebar_collapsed", next ? "1" : "0");
      return next;
    });
  }

  return (
    <div className={`app-shell${collapsed ? " sidebar-collapsed" : ""}`}>
      <Sidebar collapsed={collapsed} onToggle={toggle} />
      <Topbar onOpenSearch={() => setPalette(true)} onToggleSidebar={toggle} />
      <main className="app-main" id="main">
        {children}
      </main>
      <ResearchCommandBar />
      <CommandPalette open={palette} onClose={() => setPalette(false)} />
    </div>
  );
}

/** Status badge mapping helpers. */

import type { NodeStatus } from "@/domain/types";

export function statusBadgeClass(status: string | undefined): string {
  const s = (status ?? "pending").toLowerCase();
  if (s.includes("run") || s === "pending") {
    if (s.includes("run")) return "badge badge-running";
    return "badge badge-pending";
  }
  if (s.includes("complete") || s === "accepted" || s === "robust")
    return "badge badge-completed";
  if (s.includes("promis") || s.includes("warn") || s === "candidate")
    return "badge badge-warning";
  if (s.includes("fail")) return "badge badge-failed";
  if (s.includes("reject") || s === "retired") return "badge badge-rejected";
  if (s.includes("paper")) return "badge badge-paper";
  if (s === "live") return "badge badge-live";
  return "badge badge-pending";
}

export function toNodeStatus(status: string | undefined): NodeStatus {
  const s = (status ?? "pending").toLowerCase();
  if (s.includes("run")) return "running";
  if (s.includes("fail")) return "failed";
  if (s.includes("reject")) return "rejected";
  if (s.includes("warn")) return "warning";
  if (s.includes("complete") || s === "ok") return "completed";
  return "pending";
}

export const NAV_ITEMS = [
  { href: "/", label: "Overview", icon: "◈", group: "Core" },
  { href: "/research", label: "Research", icon: "◉", group: "Core" },
  { href: "/experiments", label: "Experiments", icon: "▦", group: "Core" },
  { href: "/alphas", label: "Alpha Library", icon: "α", group: "Core" },
  { href: "/strategies", label: "Strategies", icon: "Σ", group: "Core" },
  { href: "/portfolio", label: "Portfolio", icon: "▣", group: "Risk" },
  { href: "/risk", label: "Risk", icon: "⚠", group: "Risk" },
  { href: "/data", label: "Market Data", icon: "▥", group: "Risk" },
  { href: "/regimes", label: "Regimes", icon: "≋", group: "Risk" },
  { href: "/paper", label: "Paper Trading", icon: "⬡", group: "Ops" },
  { href: "/reports", label: "Reports", icon: "▤", group: "Ops" },
  { href: "/agents", label: "Agent Activity", icon: "◎", group: "Ops" },
  { href: "/memory", label: "Research Memory", icon: "◇", group: "Ops" },
  { href: "/system", label: "System", icon: "⚙", group: "Ops" },
] as const;

"use client";

import type { ReactNode } from "react";

export function Badge({
  status,
  children,
  className = "",
}: {
  status?: string;
  children?: ReactNode;
  className?: string;
}) {
  const s = (status ?? "pending").toLowerCase();
  let cls = "badge-pending";
  if (s.includes("run")) cls = "badge-running";
  else if (s.includes("complete") || s === "accepted" || s === "robust")
    cls = "badge-completed";
  else if (s.includes("promis") || s.includes("warn") || s === "candidate")
    cls = "badge-warning";
  else if (s.includes("fail")) cls = "badge-failed";
  else if (s.includes("reject") || s === "retired") cls = "badge-rejected";
  else if (s.includes("paper")) cls = "badge-paper";
  else if (s === "live") cls = "badge-live";
  else if (s === "backtest") cls = "badge-backtest";
  else if (s === "inferred") cls = "badge-inferred";

  return (
    <span className={`badge ${cls} ${className}`.trim()}>
      {children ?? status}
    </span>
  );
}

export function Metric({
  label,
  value,
  hint,
  tone,
  small,
}: {
  label: string;
  value: ReactNode;
  hint?: string;
  tone?: "pos" | "neg";
  small?: boolean;
}) {
  return (
    <div className="metric">
      <span className="metric-label">{label}</span>
      <span
        className={`metric-value${small ? " sm" : ""}${tone ? ` ${tone}` : ""}`}
      >
        {value}
      </span>
      {hint ? <span className="metric-hint">{hint}</span> : null}
    </div>
  );
}

export function Panel({
  title,
  actions,
  children,
  dense,
  className = "",
}: {
  title: string;
  actions?: ReactNode;
  children: ReactNode;
  dense?: boolean;
  className?: string;
}) {
  return (
    <section className={`panel ${className}`.trim()}>
      <header className="panel-header">
        <h2 className="panel-title">{title}</h2>
        {actions ? <div>{actions}</div> : null}
      </header>
      <div className={`panel-body${dense ? " dense" : ""}`}>{children}</div>
    </section>
  );
}

export function EmptyState({
  title,
  description,
  action,
}: {
  title: string;
  description: string;
  action?: ReactNode;
}) {
  return (
    <div className="empty-state">
      <h3>{title}</h3>
      <p>{description}</p>
      {action}
    </div>
  );
}

export function ErrorState({
  title,
  message,
  actions,
}: {
  title: string;
  message: string;
  actions?: ReactNode;
}) {
  return (
    <div className="error-state" role="alert">
      <h3>{title}</h3>
      <p>{message}</p>
      {actions ? <div className="error-actions">{actions}</div> : null}
    </div>
  );
}

export function SourceBanner({
  mode,
}: {
  mode: "BACKTEST" | "PAPER TRADING" | "LIVE";
}) {
  const cls =
    mode === "LIVE" ? "live" : mode === "PAPER TRADING" ? "paper" : "backtest";
  return (
    <span className={`source-banner ${cls}`} title="Data provenance mode">
      {mode}
    </span>
  );
}

export function ProgressBar({ value }: { value: number }) {
  const pct = Math.max(0, Math.min(100, value));
  return (
    <div
      className="progress-track"
      role="progressbar"
      aria-valuenow={pct}
      aria-valuemin={0}
      aria-valuemax={100}
    >
      <div className="progress-fill" style={{ width: `${pct}%` }} />
    </div>
  );
}

export function Button({
  children,
  variant = "default",
  size,
  ...rest
}: React.ButtonHTMLAttributes<HTMLButtonElement> & {
  variant?: "default" | "primary" | "ghost" | "danger";
  size?: "sm" | "lg";
}) {
  const cls = [
    "btn",
    variant === "primary" && "btn-primary",
    variant === "ghost" && "btn-ghost",
    variant === "danger" && "btn-danger",
    size === "sm" && "btn-sm",
    size === "lg" && "btn-lg",
  ]
    .filter(Boolean)
    .join(" ");
  return (
    <button type="button" className={cls} {...rest}>
      {children}
    </button>
  );
}

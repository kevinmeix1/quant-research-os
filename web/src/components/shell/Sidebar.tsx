"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { NAV_ITEMS } from "@/lib/status";

export function Sidebar({
  collapsed,
  onToggle,
}: {
  collapsed: boolean;
  onToggle: () => void;
}) {
  const pathname = usePathname();
  const groups = ["Core", "Risk", "Ops"] as const;

  return (
    <aside className="app-sidebar" aria-label="Primary">
      <div className="brand">
        <div className="brand-mark" aria-hidden />
        <div className="brand-text">
          Quant Research OS
          <span className="brand-sub">Workstation</span>
        </div>
      </div>
      <nav className="nav-section">
        {groups.map((g) => (
          <div key={g}>
            <div className="nav-label">{g}</div>
            {NAV_ITEMS.filter((i) => i.group === g).map((item) => {
              const active =
                item.href === "/"
                  ? pathname === "/"
                  : pathname.startsWith(item.href);
              return (
                <Link
                  key={item.href}
                  href={item.href}
                  className={`nav-item${active ? " active" : ""}`}
                  title={item.label}
                  aria-current={active ? "page" : undefined}
                >
                  <span className="nav-icon" aria-hidden>
                    {item.icon}
                  </span>
                  <span>{item.label}</span>
                </Link>
              );
            })}
          </div>
        ))}
      </nav>
      <div className="sidebar-footer">
        <button
          type="button"
          className="btn btn-ghost btn-sm"
          onClick={onToggle}
          aria-label={collapsed ? "Expand sidebar" : "Collapse sidebar"}
        >
          {collapsed ? "»" : "« Collapse"}
        </button>
      </div>
    </aside>
  );
}

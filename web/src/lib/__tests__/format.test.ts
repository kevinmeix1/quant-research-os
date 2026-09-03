import { describe, expect, it } from "vitest";
import { formatNum, formatPct, metricTone, shortId } from "@/lib/api";
import { statusBadgeClass, toNodeStatus } from "@/lib/status";
import { buildWorkflowFromTrace } from "@/components/research/ResearchGraph";

describe("formatters", () => {
  it("formats numbers and percents", () => {
    expect(formatNum(1.2345)).toBe("1.23");
    expect(formatNum(null)).toBe("—");
    expect(formatPct(0.125, 1)).toBe("12.5%");
    expect(shortId("ABCDEFGHIJKLMNOP", 6)).toBe("ABCDEF…");
  });

  it("metric tone", () => {
    expect(metricTone(0.5)).toBe("pos");
    expect(metricTone(-0.2)).toBe("neg");
    expect(metricTone(0)).toBeUndefined();
  });
});

describe("status helpers", () => {
  it("maps badge classes", () => {
    expect(statusBadgeClass("RUNNING")).toContain("running");
    expect(statusBadgeClass("ROBUST")).toContain("completed");
    expect(statusBadgeClass("REJECTED")).toContain("rejected");
  });

  it("maps node status", () => {
    expect(toNodeStatus("RUNNING")).toBe("running");
    expect(toNodeStatus("FAILED")).toBe("failed");
    expect(toNodeStatus("COMPLETED")).toBe("completed");
  });
});

describe("workflow graph", () => {
  it("builds nodes from agent traces", () => {
    const nodes = buildWorkflowFromTrace(
      [
        { agent: "planner", event: "completed", ts: "2026-01-01T00:00:00" },
        { agent: "data", event: "completed" },
        { agent: "backtest", event: "failed", payload: { error: "x" } },
      ],
      "RUNNING",
    );
    expect(nodes.length).toBeGreaterThan(5);
    expect(nodes.find((n) => n.id === "planner")?.status).toBe("completed");
    expect(nodes.find((n) => n.id === "backtest")?.status).toBe("failed");
  });
});

/** Typed API client for Quant Research OS backend. */

import type {
  Alpha,
  Experiment,
  HealthStatus,
  PaperPosition,
  PortfolioSummary,
  ResearchDetail,
  ResearchRequest,
  Strategy,
  AgentTrace,
  BacktestResult,
  ResearchReport,
} from "@/domain/types";

const DEFAULT_BASE =
  process.env.NEXT_PUBLIC_QROS_API_URL ?? "http://127.0.0.1:8002";

export class ApiError extends Error {
  constructor(
    message: string,
    public status: number,
    public body?: string,
  ) {
    super(message);
    this.name = "ApiError";
  }
}

function apiKey(): string | undefined {
  if (typeof window === "undefined") return process.env.NEXT_PUBLIC_QROS_API_KEY;
  return (
    process.env.NEXT_PUBLIC_QROS_API_KEY ||
    window.localStorage.getItem("qros_api_key") ||
    undefined
  );
}

async function request<T>(
  path: string,
  init?: RequestInit & { baseUrl?: string },
): Promise<T> {
  const base = init?.baseUrl ?? DEFAULT_BASE;
  const headers: Record<string, string> = {
    Accept: "application/json",
    ...(init?.headers as Record<string, string> | undefined),
  };
  const key = apiKey();
  if (key) headers["X-API-Key"] = key;
  if (init?.body && !headers["Content-Type"]) {
    headers["Content-Type"] = "application/json";
  }

  const res = await fetch(`${base}${path}`, { ...init, headers });
  if (!res.ok) {
    const body = await res.text().catch(() => "");
    throw new ApiError(
      body || `Request failed: ${res.status} ${path}`,
      res.status,
      body,
    );
  }
  if (res.status === 204) return undefined as T;
  return res.json() as Promise<T>;
}

function normalizeResearch(row: ResearchRequest): ResearchRequest {
  return {
    ...row,
    question: row.question || row.user_question || "",
  };
}

export const api = {
  health: () => request<HealthStatus>("/health"),

  listResearch: async (limit = 50) => {
    const rows = await request<ResearchRequest[]>(`/research?limit=${limit}`);
    return rows.map(normalizeResearch);
  },

  getResearch: async (id: string) => {
    const detail = await request<ResearchDetail>(
      `/research/${encodeURIComponent(id)}`,
    );
    return {
      ...detail,
      request: normalizeResearch(detail.request),
    };
  },

  getTrace: (id: string) =>
    request<AgentTrace[]>(`/research/${encodeURIComponent(id)}/trace`),

  createResearch: (body: {
    question: string;
    universe?: string;
    max_experiments?: number;
    max_hypotheses?: number;
  }) =>
    request<Record<string, unknown>>("/research", {
      method: "POST",
      body: JSON.stringify(body),
    }),

  cancelResearch: (id: string) =>
    request<{ status: string }>(`/research/${encodeURIComponent(id)}/cancel`, {
      method: "POST",
    }),

  listExperiments: (researchId?: string, limit = 200) => {
    const q = new URLSearchParams({ limit: String(limit) });
    if (researchId) q.set("research_id", researchId);
    return request<Experiment[]>(`/experiments?${q}`);
  },

  getExperiment: (id: string) =>
    request<Experiment>(`/experiments/${encodeURIComponent(id)}`),

  listAlphas: () => request<Alpha[]>("/alphas"),

  getAlpha: (id: string) =>
    request<Alpha>(`/alphas/${encodeURIComponent(id)}`),

  listStrategies: () => request<Strategy[]>("/strategies"),

  getStrategy: (id: string) =>
    request<Strategy>(`/strategies/${encodeURIComponent(id)}`),

  getBacktest: (id: string) =>
    request<BacktestResult>(`/backtests/${encodeURIComponent(id)}`),

  getReport: (id: string) =>
    request<ResearchReport>(`/reports/${encodeURIComponent(id)}`),

  portfolio: () => request<PortfolioSummary>("/portfolio"),

  portfolioRisk: () => request<Record<string, unknown>>("/portfolio/risk"),

  portfolioCorrelations: () =>
    request<Record<string, unknown>>("/portfolio/correlations"),

  listPaper: () => request<PaperPosition[]>("/paper"),

  paperStep: (alphaId: string, nDays = 21) =>
    request<Record<string, unknown>>(
      `/paper/${encodeURIComponent(alphaId)}/step?n_days=${nDays}`,
      { method: "POST" },
    ),
};

export function formatNum(
  v: number | null | undefined,
  digits = 2,
): string {
  if (v == null || Number.isNaN(v)) return "—";
  return v.toFixed(digits);
}

export function formatPct(
  v: number | null | undefined,
  digits = 1,
): string {
  if (v == null || Number.isNaN(v)) return "—";
  return `${(v * 100).toFixed(digits)}%`;
}

export function shortId(id: string | undefined, n = 10): string {
  if (!id) return "—";
  return id.length <= n ? id : `${id.slice(0, n)}…`;
}

export function metricTone(
  v: number | null | undefined,
  { higherIsBetter = true } = {},
): "pos" | "neg" | undefined {
  if (v == null || Number.isNaN(v) || v === 0) return undefined;
  const good = higherIsBetter ? v > 0 : v < 0;
  return good ? "pos" : "neg";
}

/** Domain types aligned with Quant Research OS API schemas. */

export type ResearchStatus =
  | "PENDING"
  | "RUNNING"
  | "COMPLETED"
  | "FAILED"
  | "CANCELLED"
  | "COMPLETED_WITH_WARNINGS";

export type AlphaStatus =
  | "CANDIDATE"
  | "PROMISING"
  | "ROBUST"
  | "PAPER_TRADING"
  | "REJECTED"
  | "RETIRED";

export type ExperimentStatus =
  | "PENDING"
  | "RUNNING"
  | "COMPLETED"
  | "FAILED"
  | "REJECTED"
  | "CANCELLED";

export type NodeStatus =
  | "pending"
  | "running"
  | "completed"
  | "warning"
  | "failed"
  | "rejected";

export interface ResearchRequest {
  research_id: string;
  question: string;
  user_question?: string;
  status: ResearchStatus | string;
  created_at?: string;
  universe?: string;
  max_experiments?: number;
  constraints?: Record<string, unknown>;
  [key: string]: unknown;
}

export interface ResearchPlan {
  research_id: string;
  interpreted_question?: string;
  objectives?: string[];
  constraints?: string[];
  success_criteria?: string[];
  failure_criteria?: string[];
  hypotheses?: Hypothesis[];
  [key: string]: unknown;
}

export interface Hypothesis {
  hypothesis_id: string;
  economic_mechanism?: string;
  expected_effect?: string;
  status?: string;
  [key: string]: unknown;
}

export interface ResearchReport {
  research_id: string;
  status?: string;
  executive_summary?: string;
  survivors?: string[];
  rejected?: string[];
  sections?: Record<string, unknown>;
  [key: string]: unknown;
}

export interface ResearchDetail {
  request: ResearchRequest;
  plan: ResearchPlan | null;
  report: ResearchReport | null;
  checkpoint: Record<string, unknown> | null;
}

export interface AgentTrace {
  research_id: string;
  agent?: string;
  event?: string;
  ts?: string;
  payload?: Record<string, unknown>;
  [key: string]: unknown;
}

export interface Experiment {
  experiment_id: string;
  research_id?: string;
  strategy_id?: string;
  hypothesis_id?: string;
  status: ExperimentStatus | string;
  dataset?: string;
  period_start?: string;
  period_end?: string;
  metrics?: Record<string, number | null | undefined>;
  config?: Record<string, unknown>;
  [key: string]: unknown;
}

export interface Alpha {
  alpha_id: string;
  strategy_id?: string;
  status: AlphaStatus | string;
  hypothesis?: string;
  metrics?: Record<string, number | null | undefined>;
  metrics_source_ids?: string[];
  correlation_to_existing?: number | null;
  robustness_score?: number | null;
  regime_stability?: number | null;
  [key: string]: unknown;
}

export interface Strategy {
  strategy_id: string;
  name?: string;
  family?: string;
  asset_class?: string;
  parameters?: Record<string, unknown>;
  [key: string]: unknown;
}

export interface BacktestResult {
  backtest_id: string;
  experiment_id?: string;
  equity_curve?: number[];
  drawdown_curve?: number[];
  metrics?: Record<string, number | null | undefined>;
  [key: string]: unknown;
}

export interface PortfolioSummary {
  n_alphas: number;
  by_status: Record<string, number>;
  alphas: Array<{
    alpha_id: string;
    status: string;
    sharpe?: number | null;
    hypothesis?: string;
  }>;
}

export interface PaperPosition {
  alpha_id: string;
  status?: string;
  pnl?: number;
  expected_sharpe?: number;
  realized_sharpe?: number;
  slippage?: number;
  [key: string]: unknown;
}

export interface HealthStatus {
  status: string;
  database?: boolean | string;
}

export interface WorkflowNode {
  id: string;
  label: string;
  status: NodeStatus;
  durationMs?: number;
  toolCalls?: number;
  errors?: number;
  hasOutput?: boolean;
}

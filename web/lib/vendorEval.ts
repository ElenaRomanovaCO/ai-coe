// Shared types + constants for the Vendor & Model Evaluation Center (AGENT-13, Module 13).
// Kept out of the "use server" actions file (which may only export async functions).

export const VENDOR_EVAL_AGENT_ID = "AGENT-13";

export interface EvaluationSummary {
  id: string;
  title: string;
  category: string;
  vendors_compared: string[];
  criteria: string[];
  last_verified: string;
  stale: boolean;
  age_days: number | null;
  file_path: string;
}

export interface EvaluationDetail {
  id: string;
  title: string;
  frontmatter: Record<string, unknown>;
  body_markdown: string;
  file_path: string;
  stale: boolean;
  age_days: number | null;
}

export interface ListEvaluationsResult {
  status: string;
  evaluations: EvaluationSummary[];
  message?: string;
}

export interface GetEvaluationResult {
  status: string;
  evaluation: EvaluationDetail;
  message?: string;
}

export interface ComparisonResult {
  status: string;
  comparison_id: string;
  evaluation_ids: string[];
  comparison_markdown: string;
  insights: string[];
  message?: string;
}

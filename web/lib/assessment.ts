// Maturity Assessment types, mirroring AGENT-02
// (agents/lambdas/modules/agent_02_assessment.py).

import type { AssetSummary } from "./assets";

export const ASSESSMENT_AGENT_ID = "AGENT-02";
export const ASSESSMENT_ROUTE = "/modules/maturity-assessment";

export const STAGE_NAMES = [
  "Nascent",
  "Emerging",
  "Piloting",
  "Scaling",
  "Operational",
  "Transformative",
] as const;

export interface AssessmentResult {
  assessment_id: string;
  stage: number;
  rationale: string;
  dimension_scores: Record<string, number>;
  recommendations: AssetSummary[];
  vault_file_path: string;
}

export interface StartResponse {
  status: string;
  assessment_id: string;
  is_complete: boolean;
  next_question: string;
}

export interface TurnResponse {
  status: string;
  is_complete: boolean;
  next_question?: string;
  result?: AssessmentResult;
}

export interface AssessmentSummary {
  assessment_id: string;
  status: string;
  stage: number | null;
  created_at: string;
}

export function humanizeDimension(key: string): string {
  return key.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase());
}

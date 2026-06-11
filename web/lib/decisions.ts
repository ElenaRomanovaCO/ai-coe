// Shared types + constants for the Decision Log (AGENT-18, Module 19).
// Kept out of the "use server" actions file (which may only export async functions).

export const DECISIONS_AGENT_ID = "AGENT-18";

export interface DecisionSummary {
  decision_id: string;
  decision: string;
  tags: string[];
  engagement_id?: string | null;
  outcome?: string | null;
  created_at: string;
  file_path: string;
}

export interface Decision extends DecisionSummary {
  context: string;
  alternatives: string[];
  rationale: string;
  updated_at: string;
}

export interface WriteDecisionInput {
  display_name: string;
  decision: string;
  context: string;
  alternatives: string[];
  rationale: string;
  outcome?: string | null;
  tags: string[];
  engagement_id?: string | null;
}

export interface WriteDecisionResult {
  status: string;
  decision: Decision;
  vault_file_path: string;
  message?: string;
}

export interface SearchDecisionsResult {
  status: string;
  decisions: DecisionSummary[];
  message?: string;
}

export interface GetDecisionResult {
  status: string;
  decision: Decision;
  message?: string;
}

export interface GetSimilarResult {
  status: string;
  decision_id: string;
  similar: DecisionSummary[];
  message?: string;
}

// Split a textarea / comma list into a clean array (one item per line or comma).
export function toList(text: string): string[] {
  return text
    .split(/[\n,]/)
    .map((s) => s.trim())
    .filter(Boolean);
}

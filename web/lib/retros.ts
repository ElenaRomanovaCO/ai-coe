// Shared types + constants for the Engagement Retrospective Tracker (AGENT-15, Module 16).
// Kept out of the "use server" actions file (which may only export async functions).

export const RETROS_AGENT_ID = "AGENT-15";

export interface Insight {
  insight_id: string;
  type: string;
  statement: string;
  evidence: string;
  asset_link: string | null;
  retro_id: string;
  file_path?: string;
}

export interface Retro {
  retro_id: string;
  engagement_id: string;
  use_cases_attempted: string[];
  patterns_used: string[];
  what_worked: string;
  what_failed: string;
  tools_recommended: string[];
  tools_not_recommended: string[];
  stage_reassessment: number;
  created_at: string;
}

export interface RetroSummary {
  retro_id: string;
  engagement_id: string;
  stage_reassessment: number;
  insight_count: number;
  created_at: string;
}

export interface WriteRetroInput {
  display_name: string;
  engagement_id: string;
  use_cases_attempted: string[];
  patterns_used: string[];
  what_worked: string;
  what_failed: string;
  tools_recommended: string[];
  tools_not_recommended: string[];
  stage_reassessment: number;
}

export interface WriteRetroResult {
  status: string;
  retro: Retro;
  insights: Insight[];
  message?: string;
}

export interface GetRetroResult {
  status: string;
  retro: Retro;
  insights: Insight[];
  message?: string;
}

export interface ListRetrosResult {
  status: string;
  retros: RetroSummary[];
  message?: string;
}

export const INSIGHT_TYPE_STYLE: Record<string, string> = {
  pattern: "bg-indigo-100 text-indigo-700 border-indigo-200",
  tooling: "bg-sky-100 text-sky-700 border-sky-200",
  process: "bg-emerald-100 text-emerald-700 border-emerald-200",
  risk: "bg-red-100 text-red-700 border-red-200",
  people: "bg-violet-100 text-violet-700 border-violet-200",
  general: "bg-neutral-100 text-neutral-600 border-neutral-200",
};

export function toList(text: string): string[] {
  return text
    .split(/[\n,]/)
    .map((s) => s.trim())
    .filter(Boolean);
}

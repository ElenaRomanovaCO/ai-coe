// Shared types + constants for the AI SOW Generator (AGENT-29, Module 30).
// Kept out of the "use server" actions file (which may only export async functions).

export const SOW_AGENT_ID = "AGENT-29";

export interface SowInputs {
  display_name: string;
  client_context: string;
  engagement_type: string;
  objectives: string[];
  scope_items: string[];
  deliverables: string[];
  timeline_weeks: number;
  milestones: string[];
  pricing_model: string;
  assumptions: string[];
}

export interface GenerateSowResult {
  status: string;
  sow_id: string;
  created_at: string;
  title: string;
  sections: string[];
  markdown: string;
  download_url: string | null;
  message?: string;
}

export interface GetSowResult extends GenerateSowResult {
  inputs?: Partial<SowInputs>;
}

export interface SowSummary {
  sow_id: string;
  title: string;
  engagement_type: string;
  created_at: string;
}

export interface ListSowResult {
  status: string;
  sows: SowSummary[];
  message?: string;
}

export const ENGAGEMENT_TYPES = ["assessment", "pilot", "build", "advisory"];
export const PRICING_MODELS = ["fixed", "T&M", "milestone"];

export function toList(text: string): string[] {
  return text
    .split(/[\n,]/)
    .map((s) => s.trim())
    .filter(Boolean);
}

// Shared types + constants for the AI Use Case Ideation Engine (AGENT-12, Module 12).
// Kept out of the "use server" actions file (which may only export async functions).

export const IDEATION_AGENT_ID = "AGENT-12";

export type Level = "low" | "medium" | "high";

export interface IdeationRequest {
  display_name: string;
  industry: string;
  pain_points: string[];
  goals: string[];
  available_data: string[];
  ai_stage: number;
}

// Mirrors UseCaseCandidate in agent_12_ideation.py (incl. the display helpers).
export interface UseCaseCandidate {
  id: string;
  title: string;
  description: string;
  effort: Level;
  impact: Level;
  prerequisites: string[];
  reference_example_asset_id: string | null;
  reference_example_title?: string | null;
  reference_example_url?: string | null;
  rationale: string;
  rank_score: number;
}

export interface IdeationResult {
  status: string;
  ideation_id: string;
  candidates: UseCaseCandidate[];
  vault_file_path: string;
  markdown?: string;
  request?: Partial<IdeationRequest>;
  created_at?: string;
  message?: string;
}

export const LEVEL_STYLE: Record<Level, string> = {
  high: "bg-green-100 text-green-700 border-green-200",
  medium: "bg-amber-100 text-amber-700 border-amber-200",
  low: "bg-neutral-100 text-neutral-600 border-neutral-200",
};

// Impact uses a "more is better" ramp; effort uses a "less is better" ramp.
export const IMPACT_STYLE: Record<Level, string> = LEVEL_STYLE;
export const EFFORT_STYLE: Record<Level, string> = {
  low: "bg-green-100 text-green-700 border-green-200",
  medium: "bg-amber-100 text-amber-700 border-amber-200",
  high: "bg-red-100 text-red-700 border-red-200",
};

export const INDUSTRIES = [
  "retail",
  "healthcare",
  "financial-services",
  "manufacturing",
  "energy",
  "public-sector",
  "technology",
  "cross-industry",
];

export const AI_STAGES = [0, 1, 2, 3, 4, 5];

// Split a textarea into a clean list (one item per line, commas also allowed).
export function toList(text: string): string[] {
  return text
    .split(/[\n,]/)
    .map((s) => s.trim())
    .filter(Boolean);
}

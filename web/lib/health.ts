// Shared types + constants for the AI Project Health Monitor (AGENT-17, Module 18).
// Kept out of the "use server" actions file (which may only export async functions).

export const HEALTH_AGENT_ID = "AGENT-17";

export type Band = "green" | "amber" | "red";
export type Severity = "low" | "medium" | "high";
export type UpdateType = "status" | "architecture" | "scope-change" | "blocker" | "decision";

export interface FlagReference {
  id: string;
  title?: string;
  file_path?: string;
}

export interface HealthFlag {
  severity: Severity;
  description: string;
  remediation: string;
  references: FlagReference[];
}

export interface EngagementUpdate {
  ts: string;
  update_type: UpdateType;
  text: string;
  risk_score: number;
  summary?: string;
  flags: HealthFlag[];
}

export interface EngagementSummary {
  engagement_id: string;
  name: string;
  industry: string;
  ai_stage: number;
  risk_score: number;
  band: Band;
  update_count: number;
  last_update: string;
  open_flags: number;
}

export interface EngagementDetail extends EngagementSummary {
  use_cases: string[];
  start_date: string;
  created_at: string;
  updates: EngagementUpdate[];
}

export interface RegisterInput {
  display_name: string;
  name: string;
  industry: string;
  ai_stage: number;
  use_cases: string[];
  start_date: string;
}

export interface PostUpdateInput {
  engagement_id: string;
  update_text: string;
  update_type: UpdateType;
}

export interface RegisterResult {
  status: string;
  engagement: EngagementSummary;
  message?: string;
}

export interface PostUpdateResult {
  status: string;
  engagement_id: string;
  risk_score: number;
  band: Band;
  flags: HealthFlag[];
  summary?: string;
  message?: string;
}

export interface GetEngagementResult {
  status: string;
  engagement: EngagementDetail;
  message?: string;
}

export interface PortfolioResult {
  status: string;
  engagements: EngagementSummary[];
  message?: string;
}

// --- display helpers -------------------------------------------------------
export const UPDATE_TYPES: UpdateType[] = [
  "status",
  "architecture",
  "scope-change",
  "blocker",
  "decision",
];

export const INDUSTRIES = [
  "financial-services",
  "healthcare",
  "retail",
  "manufacturing",
  "energy",
  "public-sector",
  "technology",
  "cross-industry",
];

export const BAND_STYLE: Record<Band, string> = {
  green: "bg-green-100 text-green-700 border-green-200",
  amber: "bg-amber-100 text-amber-700 border-amber-200",
  red: "bg-red-100 text-red-700 border-red-200",
};

export const BAND_DOT: Record<Band, string> = {
  green: "bg-green-500",
  amber: "bg-amber-500",
  red: "bg-red-500",
};

export const SEVERITY_STYLE: Record<Severity, string> = {
  high: "bg-red-100 text-red-700 border-red-200",
  medium: "bg-amber-100 text-amber-700 border-amber-200",
  low: "bg-neutral-100 text-neutral-600 border-neutral-200",
};

export function bandLabel(band: Band): string {
  return { green: "On track", amber: "Watch", red: "At risk" }[band] ?? band;
}

export function toList(text: string): string[] {
  return text
    .split(/[\n,]/)
    .map((s) => s.trim())
    .filter(Boolean);
}

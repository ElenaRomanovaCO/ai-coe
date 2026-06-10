// Shared types + constants for the Compliance Tracker (AGENT-24, Module 25).
// Kept out of the "use server" actions file (which may only export async functions).

export const COMPLIANCE_AGENT_ID = "AGENT-24";

// One regulation as returned by AGENT-24 `list` (mirrors ComplianceAgent._summary_of).
export interface RegulationSummary {
  id: string;
  name: string;
  geo: string;
  status: string;
  effective_date: string;
  risk_tier: string;
  industry_scope: string[];
  tags: string[];
  file_path: string;
}

// WORKER-12 reg_summarizer output, attached to the `get` response.
export interface RegSummary {
  summary: string;
  key_requirements: string[];
  sector_implications: string[];
}

export interface RegulationDetail {
  id: string;
  name: string;
  frontmatter: Record<string, unknown>;
  body_markdown: string;
  file_path: string;
}

export interface GetRegulationResult {
  status: string;
  regulation: RegulationDetail;
  summary: RegSummary;
  message?: string;
}

export interface ListRegulationsResult {
  status: string;
  regulations: RegulationSummary[];
  message?: string;
}

// WORKER-13 applicability_checker, per-clause.
export interface ApplicabilityItem {
  clause: string;
  applies: boolean;
  reason: string;
}

export interface ApplyResult {
  status: string;
  regulation: { id: string; name: string };
  use_case_description: string;
  regulation_applies: boolean;
  applicability: ApplicabilityItem[];
  narrative: string;
  message?: string;
}

export interface ApplyInput {
  reg_id: string;
  use_case_description: string;
  industry: string;
  geography: string;
}

// Display helpers. The `geo` frontmatter values are short codes.
export const GEO_LABELS: Record<string, string> = {
  eu: "European Union",
  "us-federal": "US Federal",
  "us-state-ca": "US — California",
};

export function geoLabel(geo: string): string {
  return GEO_LABELS[geo] ?? geo;
}

export const STATUS_STYLE: Record<string, string> = {
  "in-effect": "bg-green-100 text-green-700 border-green-200",
  enacted: "bg-green-100 text-green-700 border-green-200",
  proposed: "bg-amber-100 text-amber-700 border-amber-200",
  guidance: "bg-sky-100 text-sky-700 border-sky-200",
  voluntary: "bg-sky-100 text-sky-700 border-sky-200",
};

// Industry / geography option vocabularies for the Apply modal (the agent normalizes
// these to its `geo` aliases). Browse filters are derived from the data instead.
export const INDUSTRIES = [
  "healthcare",
  "financial-services",
  "retail",
  "manufacturing",
  "energy",
  "public-sector",
  "cross-industry",
];

export const GEOGRAPHIES = ["EU", "US", "California"];

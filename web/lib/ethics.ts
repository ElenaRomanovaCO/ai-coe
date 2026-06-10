// Shared types + constants for the AI Ethics & Bias Checker (AGENT-20, Module 21).
// Kept out of the "use server" actions file (which may only export async functions).

export const ETHICS_AGENT_ID = "AGENT-20";

export type Severity = "critical" | "high" | "medium" | "low";

export const SEVERITY_ORDER: Severity[] = ["critical", "high", "medium", "low"];

export interface BiasRisk {
  id: string;
  category: string;
  description: string;
  severity: Severity;
  mitigation: string;
}

export interface FrameworkMapping {
  framework: string;
  tier: string;
  reg_id: string | null;
  note: string;
}

export interface EthicsContext {
  use_case: string;
  data_types: string[];
  affected_populations: string[];
  decision_type: string;
  geography: string;
  industry: string;
}

export interface EthicsReview {
  status: string;
  review_id: string;
  created_at?: string;
  context: EthicsContext;
  bias_risks: BiasRisk[];
  fairness_considerations: string[];
  explainability_requirements: string[];
  human_oversight_recommendations: string[];
  regulatory_tier: Record<string, string>;
  frameworks: FrameworkMapping[];
  summary: string;
  vault_file_path?: string;
  message?: string;
}

export interface EthicsReviewSummary {
  review_id: string;
  use_case?: string;
  decision_type?: string;
  industry?: string;
  created_at?: string;
  risk_count?: number;
}

export const DECISION_TYPES = ["automated", "assisted", "recommendation-only"];
export const INDUSTRIES = [
  "healthcare",
  "financial-services",
  "retail",
  "manufacturing",
  "energy",
  "public-sector",
  "cross-industry",
];
export const GEOGRAPHIES = ["EU", "US", "California", "Global"];
export const DATA_TYPES = ["pii", "phi", "financial", "biometric", "behavioral", "location"];

// Tier badge colors mirror the governance priority palette.
export const TIER_STYLE: Record<string, string> = {
  unacceptable: "bg-red-100 text-red-700 border-red-200",
  high: "bg-orange-100 text-orange-700 border-orange-200",
  applicable: "bg-amber-100 text-amber-700 border-amber-200",
  limited: "bg-amber-100 text-amber-700 border-amber-200",
  minimal: "bg-neutral-100 text-neutral-600 border-neutral-200",
};

export const SEVERITY_STYLE: Record<Severity, string> = {
  critical: "bg-red-100 text-red-700 border-red-200",
  high: "bg-orange-100 text-orange-700 border-orange-200",
  medium: "bg-amber-100 text-amber-700 border-amber-200",
  low: "bg-neutral-100 text-neutral-600 border-neutral-200",
};

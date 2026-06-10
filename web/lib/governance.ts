// Shared types + constants for the Governance & Risk Checker (AGENT-05, Module 4).
// Kept out of the "use server" actions file (which may only export async functions).

export const GOVERNANCE_AGENT_ID = "AGENT-05";

export type Priority = "critical" | "high" | "medium" | "low";

export const PRIORITY_ORDER: Priority[] = ["critical", "high", "medium", "low"];

export interface RegulationMatch {
  id: string;
  name: string;
  geo?: string;
  relevance_score?: number;
  applicable_clauses?: string[];
  file_path?: string;
  tags?: string[];
}

export interface ChecklistItem {
  id: string;
  statement: string;
  priority: Priority;
  regulation_links: string[];
  rationale: string;
}

export interface GovernanceContext {
  industry: string;
  geography: string;
  data_types: string[];
  ai_use_case_type: string;
  engagement_context?: string;
}

export interface GovernanceReview {
  status: string;
  review_id: string;
  display_name?: string;
  created_at?: string;
  context: GovernanceContext;
  regulations: RegulationMatch[];
  checklist: ChecklistItem[];
  summary: string;
  vault_file_path?: string;
  message?: string;
}

export interface ReviewSummary {
  review_id: string;
  industry?: string;
  geography?: string;
  ai_use_case_type?: string;
  created_at?: string;
  item_count?: number;
}

// Form option vocabularies. Geography labels normalize to the agent's `geo` aliases.
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

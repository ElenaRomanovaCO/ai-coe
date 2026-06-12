// Shared types + constants for Knowledge Contribution (AGENT-06, Module 5).
// Kept out of the "use server" actions file (which may only export async functions).

export const CONTRIBUTE_AGENT_ID = "AGENT-06";
export const CONTRIBUTE_ROUTE = "/modules/contribute";

// Mirror AssetFrontmatter's closed vocabularies (agents/lib/schemas) so approved
// contributions validate as real Asset Library entries.
export const ASSET_TYPES = [
  "reference-architecture",
  "solution-pattern",
  "kickoff-template",
  "discovery-questionnaire",
  "workshop-agenda",
  "roi-template",
  "risk-checklist",
];

export const INDUSTRIES = [
  "financial-services",
  "healthcare",
  "retail",
  "manufacturing",
  "energy",
  "public-sector",
  "technology",
  "professional-services",
  "cross-industry",
];

export interface FlaggedSpan {
  span: string;
  offset: number;
  suggested_replacement: string;
  reason: string;
}

export interface Anonymization {
  flagged_spans: FlaggedSpan[];
  suggested_anonymized_body: string;
}

export interface DuplicateAsset {
  id: string;
  title: string;
  file_path: string;
}

export interface TagSuggestions {
  tags: string[];
  duplicates: DuplicateAsset[];
}

export interface SubmissionInput {
  display_name: string;
  title: string;
  type: string;
  industry: string;
  ai_stage: number;
  body_markdown: string;
  contributor_notes?: string;
}

export interface PendingRecord {
  status: string;
  pending_id: string;
  review_status: string;
  display_name: string;
  title: string;
  type: string;
  industry: string;
  ai_stage: number;
  body_markdown: string;
  contributor_notes: string;
  created_at: string;
  anonymization: Anonymization;
  tag_suggestions: TagSuggestions;
  approved?: { asset_id: string; file_path: string; approved_at: string };
  message?: string;
}

export interface PendingItem {
  pending_id: string;
  title: string;
  display_name: string;
  type: string;
  industry: string;
  review_status: string;
  created_at: string;
  flag_count: number;
}

export interface ListPendingResult {
  status: string;
  pending: PendingItem[];
  message?: string;
}

export interface ApproveResult {
  status: string;
  asset_id?: string;
  file_path?: string;
  message?: string;
}

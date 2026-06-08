// Shared Asset Library types, mirroring AGENT-03's wire models
// (agents/lambdas/modules/agent_03_asset_library.py).

export const ASSET_AGENT_ID = "AGENT-03";

export interface AssetSummary {
  id: string;
  title: string;
  type: string;
  industry: string;
  ai_stage: number;
  tags: string[];
  file_path: string;
  updated_at: string;
}

export interface AssetAggregates {
  average_rating: number | null;
  rating_count: number;
  flag_count: number;
  saved_count: number;
}

export interface AssetUserState {
  saved: boolean;
  rating: number | null;
  flagged: boolean;
}

export interface AssetDetail {
  status: string;
  asset: {
    summary: AssetSummary;
    body_markdown: string;
    frontmatter: Record<string, unknown>;
  };
  aggregates: AssetAggregates;
  user?: AssetUserState;
}

export interface ListAssetsResult {
  status: string;
  assets: AssetSummary[];
}

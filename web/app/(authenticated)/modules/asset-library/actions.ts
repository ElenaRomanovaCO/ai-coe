"use server";

// Server actions for the Asset Library. Each invokes AGENT-03 in the module-agents
// Lambda via the SSR role (lambda:Invoke) — the web never touches S3/Bedrock
// directly. These routes live under (authenticated), so the proxy middleware
// already gates unauthenticated callers.

import { invokeModule } from "@/lib/aws";
import {
  ASSET_AGENT_ID,
  type AssetAggregates,
  type AssetDetail,
  type ListAssetsResult,
} from "@/lib/assets";

export interface AssetFilters {
  industry?: string;
  ai_stage?: number;
  asset_type?: string;
  tags?: string[];
  query?: string;
  limit?: number;
}

export async function listAssets(filters: AssetFilters = {}): Promise<ListAssetsResult> {
  return invokeModule<ListAssetsResult>(ASSET_AGENT_ID, { op: "list_assets", ...filters });
}

export async function searchAssets(query: string, topK = 10): Promise<ListAssetsResult> {
  return invokeModule<ListAssetsResult>(ASSET_AGENT_ID, { op: "search", query, top_k: topK });
}

export async function getAsset(assetId: string, displayName?: string): Promise<AssetDetail> {
  return invokeModule<AssetDetail>(ASSET_AGENT_ID, {
    op: "get_asset",
    asset_id: assetId,
    ...(displayName ? { display_name: displayName } : {}),
  });
}

type WriteResult = AssetAggregates & { status: string; asset_id: string; [k: string]: unknown };

export async function saveAsset(
  assetId: string,
  displayName: string,
  saved: boolean,
): Promise<WriteResult> {
  return invokeModule<WriteResult>(ASSET_AGENT_ID, {
    op: "save_asset",
    asset_id: assetId,
    display_name: displayName,
    saved,
  });
}

export async function rateAsset(
  assetId: string,
  displayName: string,
  rating: number,
): Promise<WriteResult> {
  return invokeModule<WriteResult>(ASSET_AGENT_ID, {
    op: "rate_asset",
    asset_id: assetId,
    display_name: displayName,
    rating,
  });
}

export async function flagAsset(assetId: string, displayName: string): Promise<WriteResult> {
  return invokeModule<WriteResult>(ASSET_AGENT_ID, {
    op: "flag_asset",
    asset_id: assetId,
    display_name: displayName,
  });
}

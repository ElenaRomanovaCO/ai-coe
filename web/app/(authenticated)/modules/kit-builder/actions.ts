"use server";

// Server actions for the Engagement Kit Builder. Invoke AGENT-04 in the
// module-agents Lambda. Under (authenticated), so the middleware gates callers.

import { invokeModule } from "@/lib/aws";
import { KIT_AGENT_ID, type KitManifest, type VaultFile } from "@/lib/kit";

export interface KitCriteria {
  display_name: string;
  industry: string;
  ai_stage: number;
  engagement_type: string;
  duration_weeks: number;
  extra_context?: string;
}

export async function previewKit(criteria: KitCriteria): Promise<KitManifest> {
  return invokeModule<KitManifest>(KIT_AGENT_ID, { op: "preview", ...criteria });
}

export async function searchVault(
  query: string,
  contentTypes?: string[],
  limit = 12,
): Promise<{ status: string; files: VaultFile[] }> {
  return invokeModule(KIT_AGENT_ID, {
    op: "search_vault",
    query,
    content_types: contentTypes,
    limit,
  });
}

export async function generateKit(
  criteria: KitCriteria,
  files: { category: string; source_path: string }[],
): Promise<KitManifest> {
  return invokeModule<KitManifest>(KIT_AGENT_ID, { op: "generate", ...criteria, files });
}

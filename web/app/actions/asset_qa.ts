"use server";

// Server action for the Universal Asset Q&A panel. Invokes AGENT-25 in the
// module-agents Lambda via the SSR role (lambda:Invoke) — same transport as the
// Asset Library actions. Unlike the chat dock (which streams through the
// orchestrator Function URL), AGENT-25 is non-streaming: one invoke returns the
// full answer, so a plain server action is the right fit. This file lives outside
// any single module so later detail pages (Compliance, Vendor Eval, Intelligence
// Feed) can reuse the same panel.

import { invokeModule } from "@/lib/aws";
import {
  ASSET_QA_AGENT_ID,
  type AssetQARequest,
  type AssetQAResponse,
} from "@/lib/assetQa";

export async function askAsset(req: AssetQARequest): Promise<AssetQAResponse> {
  return invokeModule<AssetQAResponse>(ASSET_QA_AGENT_ID, {
    asset_id: req.asset_id,
    asset_content: req.asset_content,
    asset_frontmatter: req.asset_frontmatter,
    session_id: req.session_id,
    message: req.message,
    history: req.history,
    display_name: req.display_name,
  });
}

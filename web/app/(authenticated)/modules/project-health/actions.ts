"use server";

// Server actions for the Project Health Monitor. Invoke AGENT-17 in the module-agents
// Lambda. Under (authenticated), so the middleware gates callers. AGENT-17 is
// non-streaming (one Sonnet analysis per posted update), so a plain invoke fits.

import { invokeModule } from "@/lib/aws";
import {
  HEALTH_AGENT_ID,
  type GetEngagementResult,
  type PortfolioResult,
  type PostUpdateInput,
  type PostUpdateResult,
  type RegisterInput,
  type RegisterResult,
} from "@/lib/health";

export async function registerEngagement(input: RegisterInput): Promise<RegisterResult> {
  return invokeModule<RegisterResult>(HEALTH_AGENT_ID, { op: "register", ...input });
}

export async function postUpdate(input: PostUpdateInput): Promise<PostUpdateResult> {
  return invokeModule<PostUpdateResult>(HEALTH_AGENT_ID, { op: "update", ...input });
}

export async function getEngagement(engagementId: string): Promise<GetEngagementResult> {
  return invokeModule<GetEngagementResult>(HEALTH_AGENT_ID, {
    op: "get",
    engagement_id: engagementId,
  });
}

export async function listPortfolio(displayName: string): Promise<PortfolioResult> {
  return invokeModule<PortfolioResult>(HEALTH_AGENT_ID, { op: "list", display_name: displayName });
}

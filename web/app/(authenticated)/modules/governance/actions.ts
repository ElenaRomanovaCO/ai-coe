"use server";

// Server actions for the Governance & Risk Checker. Invoke AGENT-05 in the
// module-agents Lambda (which fans out to WORKER-04/05 via the workers Lambda).
// Under (authenticated), so the middleware gates callers.

import { invokeModule } from "@/lib/aws";
import {
  GOVERNANCE_AGENT_ID,
  type GovernanceContext,
  type GovernanceReview,
} from "@/lib/governance";

export async function runGovernanceCheck(
  input: GovernanceContext & { display_name: string },
): Promise<GovernanceReview> {
  return invokeModule<GovernanceReview>(GOVERNANCE_AGENT_ID, { op: "check", ...input });
}

export async function getReview(reviewId: string): Promise<GovernanceReview> {
  return invokeModule<GovernanceReview>(GOVERNANCE_AGENT_ID, { op: "get", review_id: reviewId });
}

export async function listReviews(
  displayName: string,
): Promise<{ status: string; reviews: import("@/lib/governance").ReviewSummary[] }> {
  return invokeModule(GOVERNANCE_AGENT_ID, { op: "list", display_name: displayName });
}

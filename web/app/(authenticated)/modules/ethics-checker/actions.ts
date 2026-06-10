"use server";

// Server actions for the AI Ethics & Bias Checker. Invoke AGENT-20 in the
// module-agents Lambda (which fans out to WORKER-08/09). Under (authenticated),
// so the middleware gates callers.

import { invokeModule } from "@/lib/aws";
import { ETHICS_AGENT_ID, type EthicsContext, type EthicsReview } from "@/lib/ethics";

export async function runEthicsReview(
  input: EthicsContext & { display_name: string },
): Promise<EthicsReview> {
  return invokeModule<EthicsReview>(ETHICS_AGENT_ID, { op: "check", ...input });
}

export async function getReview(reviewId: string): Promise<EthicsReview> {
  return invokeModule<EthicsReview>(ETHICS_AGENT_ID, { op: "get", review_id: reviewId });
}

export async function listReviews(
  displayName: string,
): Promise<{ status: string; reviews: import("@/lib/ethics").EthicsReviewSummary[] }> {
  return invokeModule(ETHICS_AGENT_ID, { op: "list", display_name: displayName });
}

"use server";

// Server actions for the Decision Log. Invoke AGENT-18 in the module-agents Lambda.
// Under (authenticated), so the middleware gates callers. AGENT-18 is non-streaming
// (one Haiku call for tag suggestions on write), so a plain invoke is the right fit —
// same transport as the ideation / compliance actions.

import { invokeModule } from "@/lib/aws";
import {
  DECISIONS_AGENT_ID,
  type GetDecisionResult,
  type GetSimilarResult,
  type SearchDecisionsResult,
  type WriteDecisionInput,
  type WriteDecisionResult,
} from "@/lib/decisions";

export async function writeDecision(input: WriteDecisionInput): Promise<WriteDecisionResult> {
  return invokeModule<WriteDecisionResult>(DECISIONS_AGENT_ID, { op: "write", ...input });
}

export async function searchDecisions(
  filters: { query?: string; tags?: string[]; industry?: string } = {},
): Promise<SearchDecisionsResult> {
  return invokeModule<SearchDecisionsResult>(DECISIONS_AGENT_ID, { op: "search", ...filters });
}

export async function getDecision(decisionId: string): Promise<GetDecisionResult> {
  return invokeModule<GetDecisionResult>(DECISIONS_AGENT_ID, { op: "get", decision_id: decisionId });
}

export async function getSimilar(decisionId: string, topK = 5): Promise<GetSimilarResult> {
  return invokeModule<GetSimilarResult>(DECISIONS_AGENT_ID, {
    op: "similar",
    decision_id: decisionId,
    top_k: topK,
  });
}

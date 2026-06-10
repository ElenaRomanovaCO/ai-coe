"use server";

// Server actions for the Vendor & Model Evaluation Center. Invoke AGENT-13 in the
// module-agents Lambda (Sonnet for the comparison insights; no workers). Under
// (authenticated), so the middleware gates callers.

import { invokeModule } from "@/lib/aws";
import {
  VENDOR_EVAL_AGENT_ID,
  type ComparisonResult,
  type GetEvaluationResult,
  type ListEvaluationsResult,
} from "@/lib/vendorEval";

export async function listEvaluations(category?: string): Promise<ListEvaluationsResult> {
  return invokeModule<ListEvaluationsResult>(VENDOR_EVAL_AGENT_ID, {
    op: "list_evaluations",
    ...(category ? { category } : {}),
  });
}

export async function getEvaluation(evaluationId: string): Promise<GetEvaluationResult> {
  return invokeModule<GetEvaluationResult>(VENDOR_EVAL_AGENT_ID, {
    op: "get_evaluation",
    evaluation_id: evaluationId,
  });
}

export async function buildComparison(
  evaluationIds: string[],
  criteria?: string[],
): Promise<ComparisonResult> {
  return invokeModule<ComparisonResult>(VENDOR_EVAL_AGENT_ID, {
    op: "build_comparison",
    evaluation_ids: evaluationIds,
    ...(criteria && criteria.length ? { criteria } : {}),
  });
}

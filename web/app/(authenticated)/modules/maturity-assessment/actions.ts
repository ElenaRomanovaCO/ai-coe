"use server";

// Server actions for the AI Maturity Assessment. Each invokes AGENT-02 in the
// module-agents Lambda via the SSR role. Under (authenticated), so the proxy
// middleware gates unauthenticated callers.

import { invokeModule } from "@/lib/aws";
import {
  ASSESSMENT_AGENT_ID,
  type AssessmentResult,
  type AssessmentSummary,
  type StartResponse,
  type TurnResponse,
} from "@/lib/assessment";

export async function startAssessment(
  displayName: string,
  clientContext?: string,
): Promise<StartResponse> {
  return invokeModule<StartResponse>(ASSESSMENT_AGENT_ID, {
    op: "start",
    display_name: displayName,
    client_context: clientContext ?? null,
  });
}

export async function answerAssessment(
  assessmentId: string,
  userAnswer: string,
): Promise<TurnResponse> {
  return invokeModule<TurnResponse>(ASSESSMENT_AGENT_ID, {
    op: "answer",
    assessment_id: assessmentId,
    user_answer: userAnswer,
  });
}

export async function getAssessment(
  assessmentId: string,
): Promise<{ status: string; is_complete: boolean; result?: AssessmentResult; next_question?: string }> {
  return invokeModule(ASSESSMENT_AGENT_ID, { op: "get", assessment_id: assessmentId });
}

export async function listAssessments(
  displayName: string,
): Promise<{ status: string; assessments: AssessmentSummary[] }> {
  return invokeModule(ASSESSMENT_AGENT_ID, { op: "list", display_name: displayName });
}

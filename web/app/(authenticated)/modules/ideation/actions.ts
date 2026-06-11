"use server";

// Server actions for the Use Case Ideation Engine. Invoke AGENT-12 in the
// module-agents Lambda. Under (authenticated), so the middleware gates callers.
// AGENT-12 is non-streaming (one LLM call to generate candidates), so a plain
// invoke is the right fit — same transport as the compliance / feed actions.

import { invokeModule } from "@/lib/aws";
import { IDEATION_AGENT_ID, type IdeationRequest, type IdeationResult } from "@/lib/ideation";

export async function generateIdeation(req: IdeationRequest): Promise<IdeationResult> {
  return invokeModule<IdeationResult>(IDEATION_AGENT_ID, { op: "generate", ...req });
}

export async function getIdeation(ideationId: string): Promise<IdeationResult> {
  return invokeModule<IdeationResult>(IDEATION_AGENT_ID, { op: "get", ideation_id: ideationId });
}

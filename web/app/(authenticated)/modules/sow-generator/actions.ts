"use server";

// Server actions for the SOW Generator. Invoke AGENT-29 in the module-agents Lambda.
// Under (authenticated), so the middleware gates callers. AGENT-29 is non-streaming
// (deterministic skeleton + one Sonnet prose pass), so a plain invoke fits.

import { invokeModule } from "@/lib/aws";
import {
  SOW_AGENT_ID,
  type GenerateSowResult,
  type GetSowResult,
  type ListSowResult,
  type SowInputs,
} from "@/lib/sow";

export async function generateSow(inputs: SowInputs): Promise<GenerateSowResult> {
  return invokeModule<GenerateSowResult>(SOW_AGENT_ID, { op: "generate", ...inputs });
}

export async function getSow(sowId: string): Promise<GetSowResult> {
  return invokeModule<GetSowResult>(SOW_AGENT_ID, { op: "get", sow_id: sowId });
}

export async function listSow(displayName: string): Promise<ListSowResult> {
  return invokeModule<ListSowResult>(SOW_AGENT_ID, { op: "list", display_name: displayName });
}

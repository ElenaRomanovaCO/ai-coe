"use server";

// Server actions for the Retrospective Tracker. Invoke AGENT-15 in the module-agents
// Lambda. Under (authenticated), so the middleware gates callers. AGENT-15 is
// non-streaming (one Sonnet insight-extraction call on write), so a plain invoke fits.

import { invokeModule } from "@/lib/aws";
import {
  RETROS_AGENT_ID,
  type GetRetroResult,
  type ListRetrosResult,
  type WriteRetroInput,
  type WriteRetroResult,
} from "@/lib/retros";

export async function writeRetro(input: WriteRetroInput): Promise<WriteRetroResult> {
  return invokeModule<WriteRetroResult>(RETROS_AGENT_ID, { op: "write", ...input });
}

export async function getRetro(retroId: string): Promise<GetRetroResult> {
  return invokeModule<GetRetroResult>(RETROS_AGENT_ID, { op: "get", retro_id: retroId });
}

export async function listRetros(displayName: string): Promise<ListRetrosResult> {
  return invokeModule<ListRetrosResult>(RETROS_AGENT_ID, { op: "list", display_name: displayName });
}

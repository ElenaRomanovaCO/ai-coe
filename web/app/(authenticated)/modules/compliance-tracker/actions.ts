"use server";

// Server actions for the Compliance Tracker. Invoke AGENT-24 in the module-agents
// Lambda (which fans out to WORKER-12/13 via the workers Lambda). Under
// (authenticated), so the middleware gates callers. Like the governance actions, this
// is a plain invoke (AGENT-24 is non-streaming).

import { invokeModule } from "@/lib/aws";
import {
  COMPLIANCE_AGENT_ID,
  type ApplyInput,
  type ApplyResult,
  type GetRegulationResult,
  type ListRegulationsResult,
} from "@/lib/compliance";

export async function listRegulations(
  filters: {
    geography?: string;
    industry?: string;
    status?: string;
    use_case_type?: string;
    query?: string;
  } = {},
): Promise<ListRegulationsResult> {
  return invokeModule<ListRegulationsResult>(COMPLIANCE_AGENT_ID, { op: "list", ...filters });
}

export async function getRegulation(regId: string): Promise<GetRegulationResult> {
  return invokeModule<GetRegulationResult>(COMPLIANCE_AGENT_ID, { op: "get", reg_id: regId });
}

export async function applyRegulation(input: ApplyInput): Promise<ApplyResult> {
  return invokeModule<ApplyResult>(COMPLIANCE_AGENT_ID, { op: "apply", ...input });
}

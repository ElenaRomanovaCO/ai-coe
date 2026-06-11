"use server";

// Server actions for the ROI Calculator. Invoke AGENT-28 in the module-agents Lambda.
// Under (authenticated), so the middleware gates callers. AGENT-28 is non-streaming
// (deterministic math + one Sonnet narrative), so a plain invoke fits.

import { invokeModule } from "@/lib/aws";
import {
  ROI_AGENT_ID,
  type CalculateRoiResult,
  type GetRoiResult,
  type ListRoiResult,
  type RoiInputs,
} from "@/lib/roi";

export async function calculateRoi(inputs: RoiInputs): Promise<CalculateRoiResult> {
  return invokeModule<CalculateRoiResult>(ROI_AGENT_ID, { op: "calculate", ...inputs });
}

export async function getRoi(roiId: string): Promise<GetRoiResult> {
  return invokeModule<GetRoiResult>(ROI_AGENT_ID, { op: "get", roi_id: roiId });
}

export async function listRoi(displayName: string): Promise<ListRoiResult> {
  return invokeModule<ListRoiResult>(ROI_AGENT_ID, { op: "list", display_name: displayName });
}

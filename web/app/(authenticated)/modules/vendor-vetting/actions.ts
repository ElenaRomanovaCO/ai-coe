"use server";

// Server actions for Vendor Vetting. Invoke AGENT-30 in the module-agents Lambda (which
// fans out to WORKER-20 via the workers Lambda). Under (authenticated), so the middleware
// gates callers. AGENT-30 is non-streaming (deterministic scorer + one Sonnet narrative).

import { invokeModule } from "@/lib/aws";
import {
  VETTING_AGENT_ID,
  type AssessResult,
  type GetVendorResult,
  type ListVendorsResult,
  type SetStatusResult,
} from "@/lib/vendorVetting";

export async function listVendors(category?: string): Promise<ListVendorsResult> {
  return invokeModule<ListVendorsResult>(VETTING_AGENT_ID, {
    op: "list",
    ...(category ? { category } : {}),
  });
}

export async function getVendor(vendorId: string): Promise<GetVendorResult> {
  return invokeModule<GetVendorResult>(VETTING_AGENT_ID, { op: "get", vendor_id: vendorId });
}

export async function assessVendor(
  vendorId: string,
  contextIndustry = "",
  dataSensitivity = "",
): Promise<AssessResult> {
  return invokeModule<AssessResult>(VETTING_AGENT_ID, {
    op: "assess",
    vendor_id: vendorId,
    context_industry: contextIndustry,
    data_sensitivity: dataSensitivity,
  });
}

export async function setVendorStatus(
  vendorId: string,
  status: string,
  note: string,
  displayName: string,
): Promise<SetStatusResult> {
  return invokeModule<SetStatusResult>(VETTING_AGENT_ID, {
    op: "set_status",
    vendor_id: vendorId,
    status,
    note,
    display_name: displayName,
  });
}

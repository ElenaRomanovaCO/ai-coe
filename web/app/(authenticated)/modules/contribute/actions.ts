"use server";

// Server actions for Knowledge Contribution. Invoke AGENT-06 in the module-agents
// Lambda. Under (authenticated), so the middleware gates callers. AGENT-06 is
// non-streaming (one Sonnet analysis pass + S3 reads/writes).

import { invokeModule } from "@/lib/aws";
import {
  type ApproveResult,
  CONTRIBUTE_AGENT_ID,
  type ListPendingResult,
  type PendingRecord,
  type SubmissionInput,
} from "@/lib/contribute";

export async function submitAsset(input: SubmissionInput): Promise<PendingRecord> {
  return invokeModule<PendingRecord>(CONTRIBUTE_AGENT_ID, { op: "submit_asset", ...input });
}

export async function listPending(status = "pending"): Promise<ListPendingResult> {
  return invokeModule<ListPendingResult>(CONTRIBUTE_AGENT_ID, { op: "list_pending", status });
}

export async function getPending(pendingId: string): Promise<PendingRecord> {
  return invokeModule<PendingRecord>(CONTRIBUTE_AGENT_ID, {
    op: "get_pending",
    pending_id: pendingId,
  });
}

export async function approveAsset(
  pendingId: string,
  finalFrontmatter: Record<string, unknown>,
  finalBody: string,
): Promise<ApproveResult> {
  return invokeModule<ApproveResult>(CONTRIBUTE_AGENT_ID, {
    op: "approve_asset",
    pending_id: pendingId,
    final_frontmatter: finalFrontmatter,
    final_body: finalBody,
  });
}

export async function rejectAsset(pendingId: string, reason: string): Promise<ApproveResult> {
  return invokeModule<ApproveResult>(CONTRIBUTE_AGENT_ID, {
    op: "reject_asset",
    pending_id: pendingId,
    reason,
  });
}

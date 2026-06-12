"use server";

// Server actions for the Client Maturity Report Portal. Invoke AGENT-14 in the
// module-agents Lambda. Under (authenticated), so the middleware gates callers.
// AGENT-14 is non-streaming (deterministic skeleton + one Sonnet prose pass), so a
// plain invoke fits. PDF export is rendered client-side from the structured sections
// (web/lib/reportPdf.tsx) — no agent/server round-trip for the document itself.

import { invokeModule } from "@/lib/aws";
import { ASSESSMENT_AGENT_ID, type AssessmentSummary } from "@/lib/assessment";
import {
  REPORT_AGENT_ID,
  type ListReportsResult,
  type ReportData,
  type SectionValue,
} from "@/lib/reports";

export async function generateReport(
  assessmentId: string,
  clientContext?: string,
): Promise<ReportData> {
  return invokeModule<ReportData>(REPORT_AGENT_ID, {
    op: "generate",
    assessment_id: assessmentId,
    ...(clientContext ? { client_context: clientContext } : {}),
  });
}

export async function getReport(reportId: string): Promise<ReportData> {
  return invokeModule<ReportData>(REPORT_AGENT_ID, { op: "get", report_id: reportId });
}

export async function listReports(displayName: string): Promise<ListReportsResult> {
  return invokeModule<ListReportsResult>(REPORT_AGENT_ID, {
    op: "list",
    display_name: displayName,
  });
}

export async function updateSection(
  reportId: string,
  section: string,
  content: SectionValue,
): Promise<ReportData> {
  return invokeModule<ReportData>(REPORT_AGENT_ID, {
    op: "update_section",
    report_id: reportId,
    section,
    content,
  });
}

// Reuse AGENT-02's list so the landing can offer "generate from a completed assessment".
export async function listMyAssessments(
  displayName: string,
): Promise<{ status: string; assessments: AssessmentSummary[] }> {
  return invokeModule<{ status: string; assessments: AssessmentSummary[] }>(
    ASSESSMENT_AGENT_ID,
    { op: "list", display_name: displayName },
  );
}

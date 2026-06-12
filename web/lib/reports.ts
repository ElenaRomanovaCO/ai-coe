// Shared types + constants for the Client Maturity Report Portal (AGENT-14, Module 14).
// Kept out of the "use server" actions file (which may only export async functions).

export const REPORT_AGENT_ID = "AGENT-14";
export const REPORT_ROUTE = "/modules/reports";

// Mirror the section taxonomy AGENT-14 emits (agent_14_report.py). Prose sections are
// strings; list sections are arrays of bullet strings.
export const LIST_SECTIONS = ["top_next_steps", "recommended_use_cases"] as const;

export type SectionValue = string | string[];

export function isListSection(key: string): boolean {
  return (LIST_SECTIONS as readonly string[]).includes(key);
}

export interface ReportData {
  status: string;
  report_id: string;
  assessment_id: string;
  title: string;
  industry: string;
  stage: number | null;
  client_context: string;
  sections: Record<string, SectionValue>;
  section_order: string[];
  section_titles: Record<string, string>;
  markdown: string;
  created_at: string;
  updated_at: string;
  message?: string;
}

export interface ReportSummary {
  report_id: string;
  assessment_id: string;
  title: string;
  industry: string;
  stage: number | null;
  created_at: string;
  updated_at: string;
}

export interface ListReportsResult {
  status: string;
  reports: ReportSummary[];
  message?: string;
}

export function sectionToText(value: SectionValue | undefined): string {
  if (Array.isArray(value)) return value.join("\n");
  return value ?? "";
}

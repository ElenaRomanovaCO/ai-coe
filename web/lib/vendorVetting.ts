// Shared types + constants for Vendor Vetting (AGENT-30 + WORKER-20, Module 31).
// Kept out of the "use server" actions file (which may only export async functions).

export const VETTING_AGENT_ID = "AGENT-30";

export type RiskTier = "low" | "medium" | "high";
export type ControlResult = "pass" | "gap" | "unknown";
export type ApprovalStatus = "approved" | "conditional" | "rejected" | "unvetted";

export interface Control {
  control: string;
  result: ControlResult;
  detail: string;
}

export interface VettingRecord {
  approval_status: ApprovalStatus;
  risk_tier: RiskTier | null;
  controls: Control[];
  gaps: string[];
  narrative: string;
  note: string;
  assessed_at: string;
}

export interface VendorSummary {
  vendor_id: string;
  category: string;
  vendors_compared: string[];
  last_verified: string;
  approval_status: ApprovalStatus;
  risk_tier: RiskTier | null;
  file_path: string;
}

export interface VendorDetail {
  vendor_id: string;
  category: string;
  vendors_compared: string[];
  last_verified: string;
  frontmatter: Record<string, unknown>;
  body_markdown: string;
  file_path: string;
}

export interface ListVendorsResult {
  status: string;
  vendors: VendorSummary[];
  message?: string;
}

export interface GetVendorResult {
  status: string;
  vendor: VendorDetail;
  vetting: VettingRecord;
  message?: string;
}

export interface AssessResult {
  status: string;
  vendor_id: string;
  risk_tier: RiskTier;
  controls: Control[];
  gaps: string[];
  approval_status: ApprovalStatus;
  narrative: string;
  message?: string;
}

export interface SetStatusResult {
  status: string;
  vendor_id: string;
  approval_status: ApprovalStatus;
  message?: string;
}

// --- display helpers -------------------------------------------------------
export const RISK_STYLE: Record<string, string> = {
  low: "bg-green-100 text-green-700 border-green-200",
  medium: "bg-amber-100 text-amber-700 border-amber-200",
  high: "bg-red-100 text-red-700 border-red-200",
};

export const RESULT_STYLE: Record<ControlResult, string> = {
  pass: "bg-green-100 text-green-700 border-green-200",
  gap: "bg-red-100 text-red-700 border-red-200",
  unknown: "bg-neutral-100 text-neutral-500 border-neutral-200",
};

export const STATUS_STYLE: Record<ApprovalStatus, string> = {
  approved: "bg-green-100 text-green-700 border-green-200",
  conditional: "bg-amber-100 text-amber-700 border-amber-200",
  rejected: "bg-red-100 text-red-700 border-red-200",
  unvetted: "bg-neutral-100 text-neutral-500 border-neutral-200",
};

export const APPROVAL_STATUSES: ApprovalStatus[] = ["approved", "conditional", "rejected"];
export const CONTEXT_INDUSTRIES = ["", "healthcare", "financial-services", "public-sector", "retail"];
export const DATA_SENSITIVITIES = ["public", "internal", "pii", "phi"];

export function riskLabel(tier: RiskTier | null): string {
  return tier ? `${tier} risk` : "unvetted";
}

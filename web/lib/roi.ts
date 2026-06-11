// Shared types + constants for the AI Project ROI Calculator (AGENT-28, Module 29).
// Kept out of the "use server" actions file (which may only export async functions).

export const ROI_AGENT_ID = "AGENT-28";

export interface RoiInputs {
  display_name: string;
  project_name: string;
  industry: string;
  build_cost_usd: number;
  run_cost_usd_yr: number;
  team_size: number;
  duration_weeks: number;
  hours_saved_yr: number;
  loaded_hourly_rate_usd: number;
  revenue_uplift_usd_yr: number;
  other_benefit_usd_yr: number;
  horizon_years: number;
}

export interface RoiResult {
  total_cost_usd: number;
  annual_value_usd: number;
  net_value_usd: number;
  roi_pct: number;
  payback_months: number | null;
  narrative: string;
}

export interface CalculateRoiResult {
  status: string;
  roi_id: string;
  created_at: string;
  inputs: RoiInputs;
  result: RoiResult;
  message?: string;
}

export interface GetRoiResult {
  status: string;
  roi_id: string;
  created_at: string;
  inputs: RoiInputs;
  result: RoiResult;
  message?: string;
}

export interface RoiSummary {
  roi_id: string;
  project_name: string;
  industry: string;
  roi_pct: number;
  payback_months: number | null;
  created_at: string;
}

export interface ListRoiResult {
  status: string;
  results: RoiSummary[];
  message?: string;
}

export const INDUSTRIES = [
  "financial-services",
  "healthcare",
  "retail",
  "manufacturing",
  "energy",
  "public-sector",
  "technology",
  "cross-industry",
];

export function formatUsd(n: number): string {
  return `$${Math.round(n).toLocaleString("en-US")}`;
}

export function paybackLabel(months: number | null): string {
  if (months === null) return "No payback at these inputs";
  if (months === 0) return "Immediate";
  if (months < 12) return `${months.toFixed(1)} months`;
  return `${(months / 12).toFixed(1)} years`;
}

export function roiBand(roiPct: number): string {
  if (roiPct >= 100) return "text-green-700";
  if (roiPct > 0) return "text-amber-700";
  return "text-red-700";
}

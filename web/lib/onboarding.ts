// Shared types + constants for the Consultant Onboarding Journey (AGENT-22, Module 23).
// Kept out of the "use server" actions file (which may only export async functions).

import type { AssetSummary } from "@/lib/assets";
import type { Expert, LearningPath } from "@/lib/community";
import type { ToolSummary } from "@/lib/tools";

export const ONBOARDING_AGENT_ID = "AGENT-22";
export const ONBOARDING_ROUTE = "/modules/onboarding";

export type OnboardingRole = "consultant" | "architect" | "data-engineer" | "pm" | "executive";
export type AiBackground = "novice" | "intermediate" | "advanced";

export interface OnboardingProfile {
  role: OnboardingRole;
  experience_years: number;
  industry_focus: string[];
  ai_background: AiBackground;
  goals: string[];
}

export interface ActionItem {
  id: string;
  title: string;
  description: string;
  week: number;
  module_route: string | null;
  done: boolean;
}

export interface OnboardingPath {
  status: string;
  user: string;
  profile: OnboardingProfile;
  top_assets: AssetSummary[];
  learning_paths: LearningPath[];
  suggested_connections: Expert[];
  key_tools: ToolSummary[];
  first_actions: ActionItem[];
  message?: string;
}

export interface SaveProfileResult {
  status: string;
  onboarding?: OnboardingProfile;
  onboarding_completed?: boolean;
  message?: string;
}

export interface GetProfileResult {
  status: string;
  onboarding: OnboardingProfile | null;
  onboarding_completed: boolean;
  checklist: Record<string, boolean>;
  message?: string;
}

export interface ChecklistResult {
  status: string;
  action_id: string;
  done: boolean;
  checklist: Record<string, boolean>;
  message?: string;
}

// Form option vocabulary (mirrors AGENT-22's Literal sets).
export const ROLE_OPTIONS: { value: OnboardingRole; label: string }[] = [
  { value: "consultant", label: "Delivery Consultant" },
  { value: "architect", label: "Solution Architect" },
  { value: "data-engineer", label: "Data / ML Engineer" },
  { value: "pm", label: "Project / Program Manager" },
  { value: "executive", label: "Executive / Leadership" },
];

export const BACKGROUND_OPTIONS: { value: AiBackground; label: string }[] = [
  { value: "novice", label: "Novice — new to AI delivery" },
  { value: "intermediate", label: "Intermediate — shipped a few" },
  { value: "advanced", label: "Advanced — deep AI experience" },
];

// A reasonable industry set to choose focus from (matches seeded asset industries).
export const INDUSTRY_OPTIONS = [
  "healthcare",
  "financial-services",
  "insurance",
  "retail",
  "manufacturing",
  "public-sector",
  "technology",
  "energy",
];

export function humanizeIndustry(s: string): string {
  return s.replace(/-/g, " ").replace(/\b\w/g, (c) => c.toUpperCase());
}

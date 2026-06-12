// Shared types + constants for the Community & Enablement Hub (AGENT-07, Module 6).
// Kept out of the "use server" actions file (which may only export async functions).

export const COMMUNITY_AGENT_ID = "AGENT-07";
export const COMMUNITY_ROUTE = "/modules/community";

export interface LearningPath {
  id: string;
  title: string;
  role: string;
  stage: number | null;
  duration: string;
  modules: string[];
  tags: string[];
}

export interface OfficeHour {
  id: string;
  title: string;
  host: string;
  date: string;
  topic: string;
  capacity: number | null;
  tags: string[];
  signed_up: boolean;
}

export interface Expert {
  id: string;
  name: string;
  title: string;
  expertise: string[];
  industries: string[];
  tags: string[];
}

export interface OverviewResult {
  status: string;
  learning_paths_count: number;
  office_hours_count: number;
  experts_count: number;
  message?: string;
}

export interface LearningPathsResult {
  status: string;
  learning_paths: LearningPath[];
  message?: string;
}

export interface OfficeHoursResult {
  status: string;
  office_hours: OfficeHour[];
  message?: string;
}

export interface ExpertsResult {
  status: string;
  experts: Expert[];
  message?: string;
}

export interface SignupResult {
  status: string;
  office_hour_id: string;
  signed_up: boolean;
  signups: string[];
  message?: string;
}

// Role options for the learning-path filter (mirrors the seeded paths).
export const LEARNING_ROLES = [
  "solution-architect",
  "delivery-lead",
  "data-scientist",
  "executive",
  "engineer",
];

export function humanizeRole(role: string): string {
  return role.replace(/-/g, " ").replace(/\b\w/g, (c) => c.toUpperCase());
}

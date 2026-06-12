"use server";

// Server actions for the Community & Enablement Hub. Invoke AGENT-07 in the
// module-agents Lambda. Under (authenticated), so the middleware gates callers.
// AGENT-07 is mechanical (S3 reads + a profile-write signup), non-streaming.

import { invokeModule } from "@/lib/aws";
import {
  COMMUNITY_AGENT_ID,
  type ExpertsResult,
  type LearningPathsResult,
  type OfficeHoursResult,
  type OverviewResult,
  type SignupResult,
} from "@/lib/community";

export async function getCommunityOverview(): Promise<OverviewResult> {
  return invokeModule<OverviewResult>(COMMUNITY_AGENT_ID, {});
}

export async function listLearningPaths(
  role?: string,
  stage?: number,
): Promise<LearningPathsResult> {
  return invokeModule<LearningPathsResult>(COMMUNITY_AGENT_ID, {
    op: "list_learning_paths",
    ...(role ? { role } : {}),
    ...(stage !== undefined ? { stage } : {}),
  });
}

export async function listOfficeHours(displayName?: string): Promise<OfficeHoursResult> {
  return invokeModule<OfficeHoursResult>(COMMUNITY_AGENT_ID, {
    op: "list_office_hours",
    ...(displayName ? { display_name: displayName } : {}),
  });
}

export async function signupOfficeHours(
  displayName: string,
  officeHourId: string,
  cancel = false,
): Promise<SignupResult> {
  return invokeModule<SignupResult>(COMMUNITY_AGENT_ID, {
    op: cancel ? "cancel_office_hours" : "signup_office_hours",
    display_name: displayName,
    office_hour_id: officeHourId,
  });
}

export async function getExpertDirectory(
  expertise?: string,
  industry?: string,
): Promise<ExpertsResult> {
  return invokeModule<ExpertsResult>(COMMUNITY_AGENT_ID, {
    op: "get_expert_directory",
    ...(expertise ? { expertise } : {}),
    ...(industry ? { industry } : {}),
  });
}

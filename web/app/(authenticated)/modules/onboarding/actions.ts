"use server";

// Server actions for the Consultant Onboarding Journey. Invoke AGENT-22 in the
// module-agents Lambda. Under (authenticated), so the middleware gates callers.
// AGENT-22 is mechanical (S3 reads + a profile read-modify-write), non-streaming.

import { invokeModule } from "@/lib/aws";
import {
  type ChecklistResult,
  type GetProfileResult,
  ONBOARDING_AGENT_ID,
  type OnboardingPath,
  type OnboardingProfile,
  type SaveProfileResult,
} from "@/lib/onboarding";

export async function generateOnboardingPath(
  displayName: string,
  profile?: Partial<OnboardingProfile>,
): Promise<OnboardingPath> {
  return invokeModule<OnboardingPath>(ONBOARDING_AGENT_ID, {
    op: "generate_path",
    display_name: displayName,
    ...(profile ?? {}),
  });
}

export async function saveOnboardingProfile(
  displayName: string,
  profile: OnboardingProfile,
): Promise<SaveProfileResult> {
  return invokeModule<SaveProfileResult>(ONBOARDING_AGENT_ID, {
    op: "save_profile",
    display_name: displayName,
    ...profile,
  });
}

export async function getOnboardingProfile(displayName: string): Promise<GetProfileResult> {
  return invokeModule<GetProfileResult>(ONBOARDING_AGENT_ID, {
    op: "get_profile",
    display_name: displayName,
  });
}

export async function updateChecklistItem(
  displayName: string,
  actionId: string,
  done: boolean,
): Promise<ChecklistResult> {
  return invokeModule<ChecklistResult>(ONBOARDING_AGENT_ID, {
    op: "update_checklist",
    display_name: displayName,
    action_id: actionId,
    done,
  });
}

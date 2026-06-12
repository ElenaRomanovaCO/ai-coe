"use server";

// Server actions for the Trainings catalog. Invoke AGENT-31 in the module-agents
// Lambda. Under (authenticated), so the middleware gates callers. AGENT-31 is
// mechanical (S3 reads + a profile-write save), non-streaming.

import { invokeModule } from "@/lib/aws";
import {
  type GetTrainingResult,
  type ListTrainingsResult,
  type SaveTrainingResult,
  TRAININGS_AGENT_ID,
} from "@/lib/trainings";

interface ListFilters {
  theme?: string;
  source?: string;
  level?: string;
  kind?: string;
  query?: string;
}

export async function listTrainings(
  filters: ListFilters = {},
  displayName?: string,
): Promise<ListTrainingsResult> {
  const args: Record<string, unknown> = { op: "list" };
  for (const [k, v] of Object.entries(filters)) if (v) args[k] = v;
  if (displayName) args.display_name = displayName;
  return invokeModule<ListTrainingsResult>(TRAININGS_AGENT_ID, args);
}

export async function getTraining(
  trainingId: string,
  displayName?: string,
): Promise<GetTrainingResult> {
  return invokeModule<GetTrainingResult>(TRAININGS_AGENT_ID, {
    op: "get",
    training_id: trainingId,
    ...(displayName ? { display_name: displayName } : {}),
  });
}

export async function saveTraining(
  displayName: string,
  trainingId: string,
  unsave = false,
): Promise<SaveTrainingResult> {
  return invokeModule<SaveTrainingResult>(TRAININGS_AGENT_ID, {
    op: unsave ? "unsave" : "save",
    display_name: displayName,
    training_id: trainingId,
  });
}

export async function listSavedTrainings(displayName: string): Promise<ListTrainingsResult> {
  return invokeModule<ListTrainingsResult>(TRAININGS_AGENT_ID, {
    op: "list_saved",
    display_name: displayName,
  });
}

"use server";

// Server actions for the Prompt Engineering Studio. Invoke AGENT-11 in the
// module-agents Lambda (Sonnet for run/suggest; no workers). Under (authenticated),
// so the middleware gates callers. run_prompt is non-streaming (one invoke returns
// the full output + metrics).

import { invokeModule } from "@/lib/aws";
import {
  PROMPT_AGENT_ID,
  type PromptDetail,
  type PromptSummary,
  type RunResult,
  type SuggestResult,
} from "@/lib/prompts";

export async function listPrompts(filters: {
  use_case?: string;
  model_target?: string;
  query?: string;
} = {}): Promise<{ status: string; prompts: PromptSummary[] }> {
  return invokeModule(PROMPT_AGENT_ID, { op: "list_prompts", ...filters });
}

export async function getPrompt(
  promptId: string,
): Promise<{ status: string; prompt: PromptDetail; message?: string }> {
  return invokeModule(PROMPT_AGENT_ID, { op: "get_prompt", prompt_id: promptId });
}

export async function savePrompt(input: {
  mode: "new" | "version" | "fork";
  source_id?: string;
  title: string;
  use_case: string;
  model_targets: string[];
  variables: string[];
  prompt_text: string;
  display_name: string;
}): Promise<{ status: string; prompt: PromptSummary; message?: string }> {
  return invokeModule(PROMPT_AGENT_ID, { op: "save_prompt", ...input });
}

export async function runPrompt(input: {
  prompt_text: string;
  variables: Record<string, string>;
  model_id: string;
  max_tokens?: number;
  temperature?: number;
}): Promise<RunResult> {
  return invokeModule<RunResult>(PROMPT_AGENT_ID, { op: "run_prompt", ...input });
}

export async function suggestImprovements(input: {
  prompt_text: string;
  variables: string[];
}): Promise<SuggestResult> {
  return invokeModule<SuggestResult>(PROMPT_AGENT_ID, { op: "suggest_improvements", ...input });
}

export async function versionHistory(
  promptId: string,
): Promise<{ status: string; root_id?: string; versions: PromptSummary[] }> {
  return invokeModule(PROMPT_AGENT_ID, { op: "version_history", prompt_id: promptId });
}

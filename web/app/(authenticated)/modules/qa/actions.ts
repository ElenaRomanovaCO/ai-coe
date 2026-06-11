"use server";

// Server actions for Q&A. Invoke AGENT-09 in the module-agents Lambda (Sonnet for AI
// mode; no workers). Under (authenticated), so the middleware gates callers.
// answer_with_citations is non-streaming (one invoke returns the full answer).

import { invokeModule } from "@/lib/aws";
import {
  QA_AGENT_ID,
  type AnswerResult,
  type ThreadDetail,
  type ThreadSummary,
} from "@/lib/qa";

export async function listThreads(filters: {
  tag?: string;
  query?: string;
  sort?: string;
} = {}): Promise<{ status: string; threads: ThreadSummary[] }> {
  return invokeModule(QA_AGENT_ID, { op: "list_threads", ...filters });
}

export async function getThread(
  threadId: string,
  displayName?: string,
): Promise<{ status: string; thread: ThreadDetail; message?: string }> {
  return invokeModule(QA_AGENT_ID, {
    op: "get_thread",
    thread_id: threadId,
    ...(displayName ? { display_name: displayName } : {}),
  });
}

export async function postThread(input: {
  question: string;
  tags: string[];
  display_name: string;
  initial_answer?: string;
}): Promise<{ status: string; thread: ThreadSummary; message?: string }> {
  return invokeModule(QA_AGENT_ID, { op: "post_thread", ...input });
}

export async function answerThread(input: {
  thread_id: string;
  answer_text: string;
  display_name: string;
}): Promise<{ status: string; thread: ThreadSummary; message?: string }> {
  return invokeModule(QA_AGENT_ID, { op: "answer_thread", ...input });
}

export async function upvote(input: {
  thread_id: string;
  answer_id: string;
  display_name: string;
}): Promise<{ status: string; upvotes: number; voted: boolean; message?: string }> {
  return invokeModule(QA_AGENT_ID, { op: "upvote", ...input });
}

export async function answerWithCitations(input: {
  question: string;
  context_filters?: Record<string, unknown>;
}): Promise<AnswerResult> {
  return invokeModule<AnswerResult>(QA_AGENT_ID, { op: "answer_with_citations", ...input });
}

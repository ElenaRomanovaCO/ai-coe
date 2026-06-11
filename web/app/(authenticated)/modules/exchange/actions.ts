"use server";

// Server actions for the Agentic Skills & Plugin Exchange. Each invokes AGENT-27 in the
// module-agents Lambda via the SSR role — a read-only catalog, structurally identical to
// the Asset Library actions. Under (authenticated), so the middleware gates callers.

import { invokeModule } from "@/lib/aws";
import {
  EXCHANGE_AGENT_ID,
  type GetEntryResult,
  type ListExchangeResult,
} from "@/lib/exchange";

export async function listExchange(
  filters: { tool?: string; category?: string; query?: string } = {},
): Promise<ListExchangeResult> {
  return invokeModule<ListExchangeResult>(EXCHANGE_AGENT_ID, { op: "list", ...filters });
}

export async function searchExchange(query: string, topK = 10): Promise<ListExchangeResult> {
  return invokeModule<ListExchangeResult>(EXCHANGE_AGENT_ID, { op: "search", query, top_k: topK });
}

export async function getEntry(entryId: string): Promise<GetEntryResult> {
  return invokeModule<GetEntryResult>(EXCHANGE_AGENT_ID, { op: "get", entry_id: entryId });
}

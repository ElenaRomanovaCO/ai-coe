"use server";

// Server actions for the Skills & Tools Repository. Invoke AGENT-08 in the
// module-agents Lambda (read-only, no workers). Under (authenticated), so the
// middleware gates callers.

import { invokeModule } from "@/lib/aws";
import {
  TOOLS_AGENT_ID,
  type GetToolResult,
  type ListToolsResult,
} from "@/lib/tools";

export async function listTools(
  filters: {
    category?: string;
    stack?: string;
    stage?: number;
    cost?: string;
    query?: string;
  } = {},
): Promise<ListToolsResult> {
  return invokeModule<ListToolsResult>(TOOLS_AGENT_ID, { op: "list_tools", ...filters });
}

export async function getTool(toolId: string): Promise<GetToolResult> {
  return invokeModule<GetToolResult>(TOOLS_AGENT_ID, { op: "get_tool", tool_id: toolId });
}

export async function recommendTools(
  input: { query: string; category?: string; stage?: number; cost?: string },
): Promise<ListToolsResult> {
  return invokeModule<ListToolsResult>(TOOLS_AGENT_ID, {
    op: "recommend_tools_for_context",
    ...input,
  });
}

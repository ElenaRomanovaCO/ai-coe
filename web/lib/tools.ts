// Shared types + constants for the Skills & Tools Repository (AGENT-08, Module 7).
// Kept out of the "use server" actions file (which may only export async functions).

export const TOOLS_AGENT_ID = "AGENT-08";

// One tool as returned by AGENT-08 list/recommend (mirrors ToolSummary in agent_08_tools.py).
export interface ToolSummary {
  id: string;
  name: string;
  category: string;
  stack: string[];
  ai_stage_fit: number[];
  cost_model: string;
  tags: string[];
  file_path: string;
}

export interface ToolDetail {
  summary: ToolSummary;
  body_markdown: string;
  frontmatter: Record<string, unknown>;
}

export interface ListToolsResult {
  status: string;
  tools: ToolSummary[];
  message?: string;
}

export interface GetToolResult {
  status: string;
  tool: ToolDetail;
  message?: string;
}

// Friendly labels for the cost-model facet values.
export const COST_LABELS: Record<string, string> = {
  "open-source": "Open source",
  "usage-based": "Usage-based",
  subscription: "Subscription",
  free: "Free",
};

export function costLabel(cost: string): string {
  return COST_LABELS[cost] ?? cost.replace(/-/g, " ");
}

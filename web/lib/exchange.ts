// Shared types + constants for the Agentic Skills & Plugin Exchange (AGENT-27, Module 28).
// Kept out of the "use server" actions file (which may only export async functions).

export const EXCHANGE_AGENT_ID = "AGENT-27";

export interface ExchangeEntry {
  id: string;
  name: string;
  tool: string;
  category: string;
  summary: string;
  tags: string[];
  install: string;
  source_url?: string;
  body_markdown?: string; // populated on get
  file_path?: string;
}

export interface ListExchangeResult {
  status: string;
  entries: ExchangeEntry[];
  message?: string;
}

export interface GetEntryResult {
  status: string;
  entry: ExchangeEntry;
  frontmatter?: Record<string, unknown>;
  message?: string;
}

// --- display helpers -------------------------------------------------------
export const TOOL_LABELS: Record<string, string> = {
  "claude-code": "Claude Code",
  "claude-cowork": "Claude Cowork",
  copilot: "GitHub Copilot",
  kiro: "Kiro",
  google: "Google",
  generic: "Cross-tool",
};

export function toolLabel(tool: string): string {
  return TOOL_LABELS[tool] ?? tool.replace(/-/g, " ");
}

export const CATEGORY_LABELS: Record<string, string> = {
  skill: "Skill",
  "slash-command": "Slash command",
  "mcp-server": "MCP server",
  plugin: "Plugin",
  "prompt-pack": "Prompt pack",
  config: "Config",
};

export function categoryLabel(category: string): string {
  return CATEGORY_LABELS[category] ?? category.replace(/-/g, " ");
}

export const TOOL_STYLE: Record<string, string> = {
  "claude-code": "bg-indigo-100 text-indigo-700 border-indigo-200",
  "claude-cowork": "bg-violet-100 text-violet-700 border-violet-200",
  copilot: "bg-sky-100 text-sky-700 border-sky-200",
  kiro: "bg-emerald-100 text-emerald-700 border-emerald-200",
  google: "bg-blue-100 text-blue-700 border-blue-200",
  generic: "bg-neutral-100 text-neutral-600 border-neutral-200",
};

export const CATEGORY_STYLE: Record<string, string> = {
  skill: "bg-amber-100 text-amber-700 border-amber-200",
  "slash-command": "bg-rose-100 text-rose-700 border-rose-200",
  "mcp-server": "bg-cyan-100 text-cyan-700 border-cyan-200",
  plugin: "bg-lime-100 text-lime-700 border-lime-200",
  "prompt-pack": "bg-fuchsia-100 text-fuchsia-700 border-fuchsia-200",
  config: "bg-neutral-100 text-neutral-600 border-neutral-200",
};

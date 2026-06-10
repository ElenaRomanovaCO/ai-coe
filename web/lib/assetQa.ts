// Shared types + constants for the Universal Asset Q&A panel (AGENT-25, Module 26).
// Kept out of the "use server" action file because a server-action module may only
// export async functions. Imported by both the server action and the panel UI.

export const ASSET_QA_AGENT_ID = "AGENT-25";

// One side of a client-kept transcript turn. The panel passes the running history
// to the agent each turn (the agent is non-streaming and otherwise stateless).
export interface AssetQATurn {
  role: "user" | "assistant";
  text: string;
}

// Mirrors AssetCitation in agent_25_asset_qa.py. The asset in context is always the
// first citation; others appear when the user reaches for compare/search tools.
export interface AssetQACitation {
  asset_id: string;
  title?: string;
  file_path?: string;
  content_type?: string;
  asset_library_url?: string | null;
}

export interface AssetQAResponse {
  status: string;
  assistant_message: string;
  citations: AssetQACitation[];
  suggestions: string[];
  message?: string; // present on status: "error"
}

export interface AssetQARequest {
  asset_id: string;
  asset_content: string;
  asset_frontmatter: Record<string, unknown>;
  session_id: string;
  message: string;
  history: AssetQATurn[];
  display_name: string;
}

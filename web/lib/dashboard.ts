// Dashboard types, mirroring AGENT-16's DashboardSummary
// (agents/lambdas/modules/agent_16_dashboard.py).

import type { AssetSummary } from "./assets";

export interface ChatSession {
  session_id: string;
  snippet: string;
  updated_at: string;
  message_count: number;
}

export interface DashboardSummary {
  status?: string;
  saved_assets: AssetSummary[];
  recent_chats: ChatSession[];
  active_engagements: unknown[];
  learning_progress: unknown[];
  recommendations: AssetSummary[];
  last_session_id: string | null;
}

// Custom event the dashboard dispatches to open the chat dock (the dock listens).
export const OPEN_CHAT_EVENT = "aicoe:open-chat";

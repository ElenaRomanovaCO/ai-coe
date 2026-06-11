// Shared types + constants for the AI Intelligence Feed & Radar (AGENT-23, Module 24).
// Kept out of the "use server" actions file (which may only export async functions).
// Imported by both the server actions and the browse/detail/radar UI.

export const FEED_AGENT_ID = "AGENT-23";

// A user "profile" for personalization. The app has no persistent profile store, so
// these are chosen via UI selectors (same pattern as kit-builder / ethics / governance)
// and passed to the agent: industries + tech focus drive WORKER-10 ranking, and all
// three drive WORKER-11's tailored commentary.
export interface FeedProfile {
  industries: string[];
  ai_stage?: number | null;
  tech_focus?: string[];
}

// One feed item as returned by AGENT-23 `list` / `radar` (mirrors FeedAgent._summary_of,
// plus the relevance fields the `list` op attaches per WORKER-10).
export interface FeedItemSummary {
  id: string;
  title: string;
  category: string;
  industries: string[];
  tags: string[];
  radar_status: string | null;
  published_at: string;
  source_url: string;
  file_path: string;
  relevance_score?: number;
  matched?: { industries?: string[]; tags?: string[] };
}

export interface FeedItemDetail {
  id: string;
  title: string;
  frontmatter: Record<string, unknown>;
  body_markdown: string;
  file_path: string;
}

// WORKER-11 commentary attached to the `get` response.
export interface FeedCommentary {
  commentary: string;
  industry: string;
  ai_stage: number | null;
  tailored: boolean;
}

export interface ListFeedResult {
  status: string;
  items: FeedItemSummary[];
  message?: string;
}

export interface GetFeedItemResult {
  status: string;
  item: FeedItemDetail;
  summary: FeedItemSummary;
  commentary: FeedCommentary;
  message?: string;
}

export interface RadarViewResult {
  status: string;
  adopt: FeedItemSummary[];
  trial: FeedItemSummary[];
  assess: FeedItemSummary[];
  hold: FeedItemSummary[];
  message?: string;
}

// --- display helpers -------------------------------------------------------
export const CATEGORY_LABELS: Record<string, string> = {
  "model-release": "Model release",
  "tool-launch": "Tool launch",
  research: "Research",
  "vendor-update": "Vendor update",
  "industry-news": "Industry news",
};

export function categoryLabel(category: string): string {
  return CATEGORY_LABELS[category] ?? category.replace(/-/g, " ");
}

export const CATEGORY_STYLE: Record<string, string> = {
  "model-release": "bg-violet-100 text-violet-700 border-violet-200",
  "tool-launch": "bg-sky-100 text-sky-700 border-sky-200",
  research: "bg-amber-100 text-amber-700 border-amber-200",
  "vendor-update": "bg-emerald-100 text-emerald-700 border-emerald-200",
  "industry-news": "bg-neutral-100 text-neutral-600 border-neutral-200",
};

// Radar quadrants, in conventional Adopt → Hold order, with their cards' accent.
export const RADAR_QUADRANTS: { key: "adopt" | "trial" | "assess" | "hold"; label: string; blurb: string; accent: string }[] = [
  { key: "adopt", label: "Adopt", blurb: "Proven — use by default", accent: "border-green-300 bg-green-50" },
  { key: "trial", label: "Trial", blurb: "Promising — pilot on a real workload", accent: "border-sky-300 bg-sky-50" },
  { key: "assess", label: "Assess", blurb: "Worth understanding — track closely", accent: "border-amber-300 bg-amber-50" },
  { key: "hold", label: "Hold", blurb: "Not yet — proceed with caution", accent: "border-neutral-300 bg-neutral-50" },
];

export const RADAR_STATUS_STYLE: Record<string, string> = {
  adopt: "bg-green-100 text-green-700 border-green-200",
  trial: "bg-sky-100 text-sky-700 border-sky-200",
  assess: "bg-amber-100 text-amber-700 border-amber-200",
  hold: "bg-neutral-100 text-neutral-600 border-neutral-200",
};

// Industry options for the personalization selector. Mirrors the feed seed data's
// `industries` vocabulary (the agent treats cross-industry as broadly relevant).
export const FEED_INDUSTRIES = [
  "cross-industry",
  "technology",
  "healthcare",
  "financial-services",
  "public-sector",
];

// AI maturity stage focus (0-5), matching the platform-wide stage model.
export const AI_STAGES = [0, 1, 2, 3, 4, 5];

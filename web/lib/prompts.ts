// Shared types + constants for the Prompt Engineering Studio (AGENT-11, Module 11).
// Kept out of the "use server" actions file (which may only export async functions).

export const PROMPT_AGENT_ID = "AGENT-11";

export interface PromptSummary {
  id: string;
  title: string;
  use_case: string;
  model_targets: string[];
  variables: string[];
  version: number;
  parent_id: string | null;
  source: "seed" | "user";
  created_by?: string;
  created_at?: string;
}

export interface PromptDetail extends PromptSummary {
  prompt_text: string;
  body_markdown: string;
}

export interface RunResult {
  status: string;
  output: string;
  tokens_in: number;
  tokens_out: number;
  cost_usd: number;
  latency_ms: number;
  model_id: string;
  message?: string;
}

export interface AntiPattern {
  flag: string;
  detail: string;
}

export interface SuggestResult {
  status: string;
  suggestions: string[];
  anti_patterns: AntiPattern[];
  message?: string;
}

// Model selector options for the runner. Tier keys map to model ids server-side
// (lib_models.TIER_TO_MODEL_ID). Opus carries a daily cost cap.
export const MODEL_OPTIONS: { value: string; label: string; note?: string }[] = [
  { value: "sonnet-4-6", label: "Claude Sonnet 4.6" },
  { value: "haiku-4-5", label: "Claude Haiku 4.5" },
  { value: "opus-4-7", label: "Claude Opus 4.7", note: "subject to daily cap" },
];

// --- side-by-side line diff (no external dependency) -----------------------
export type DiffOp = "equal" | "add" | "remove";
export interface DiffRow {
  op: DiffOp;
  left: string | null;
  right: string | null;
}

// Longest-common-subsequence line diff → aligned rows for a two-column view.
export function lineDiff(a: string, b: string): DiffRow[] {
  const left = a.split("\n");
  const right = b.split("\n");
  const n = left.length;
  const m = right.length;
  // LCS table.
  const lcs: number[][] = Array.from({ length: n + 1 }, () => new Array(m + 1).fill(0));
  for (let i = n - 1; i >= 0; i--) {
    for (let j = m - 1; j >= 0; j--) {
      lcs[i][j] =
        left[i] === right[j] ? lcs[i + 1][j + 1] + 1 : Math.max(lcs[i + 1][j], lcs[i][j + 1]);
    }
  }
  const rows: DiffRow[] = [];
  let i = 0;
  let j = 0;
  while (i < n && j < m) {
    if (left[i] === right[j]) {
      rows.push({ op: "equal", left: left[i], right: right[j] });
      i++;
      j++;
    } else if (lcs[i + 1][j] >= lcs[i][j + 1]) {
      rows.push({ op: "remove", left: left[i], right: null });
      i++;
    } else {
      rows.push({ op: "add", left: null, right: right[j] });
      j++;
    }
  }
  while (i < n) rows.push({ op: "remove", left: left[i++], right: null });
  while (j < m) rows.push({ op: "add", left: null, right: right[j++] });
  return rows;
}

// Key used to stash a prompt's last run output client-side (for the diff page).
export function lastRunKey(promptId: string): string {
  return `prompt-run:${promptId}`;
}

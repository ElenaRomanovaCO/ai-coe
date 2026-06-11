// Shared types + constants for Q&A (AGENT-09, Module 8).
// Kept out of the "use server" actions file (which may only export async functions).

export const QA_AGENT_ID = "AGENT-09";

export type Confidence = "high" | "medium" | "low";

export interface ThreadSummary {
  id: string;
  question: string;
  tags: string[];
  posted_by: string;
  posted_at: string;
  answer_count: number;
  score: number;
}

export interface Answer {
  id: string;
  text: string;
  posted_by: string;
  posted_at: string;
  upvotes: number;
  voted: boolean;
}

export interface ThreadDetail {
  id: string;
  question: string;
  tags: string[];
  posted_by: string;
  posted_at: string;
  answers: Answer[];
  score: number;
}

export interface QaCitation {
  id: string;
  title: string;
  content_type: string;
  file_path: string;
  url: string | null;
}

export interface RelatedThread {
  id: string;
  question: string;
  url: string | null;
}

export interface AnswerResult {
  status: string;
  answer: string;
  citations: QaCitation[];
  confidence: Confidence;
  related_threads: RelatedThread[];
  message?: string;
}

// Starter questions for AI mode — clicking one fills the box (the [bracket] is
// auto-selected so the user can type their topic straight over it).
export const SUGGESTED_QUESTIONS: string[] = [
  "How can I use AI for [your use case]?",
  "What can AI do to help me with [a task]?",
  "What are the risks of using AI for [a use case]?",
  "Which tools fit [your scenario]?",
  "What regulations apply to AI in [your industry]?",
];

export const SORT_OPTIONS: { value: string; label: string }[] = [
  { value: "recent", label: "Most recent" },
  { value: "upvotes", label: "Most upvoted" },
  { value: "unanswered", label: "Unanswered" },
];

export const CONFIDENCE_STYLE: Record<Confidence, string> = {
  high: "bg-green-100 text-green-700 border-green-200",
  medium: "bg-amber-100 text-amber-700 border-amber-200",
  low: "bg-neutral-100 text-neutral-600 border-neutral-200",
};

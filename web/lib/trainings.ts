// Shared types + constants for the Trainings catalog (AGENT-31, Module 32).
// Kept out of the "use server" actions file (which may only export async functions).

export const TRAININGS_AGENT_ID = "AGENT-31";
export const TRAININGS_ROUTE = "/modules/trainings";

export interface TrainingSummary {
  id: string;
  title: string;
  summary: string;
  kind: string; // "hosted" | "tutorial"
  theme: string;
  source: string;
  level: string; // beginner | intermediate | advanced
  url: string;
  duration_min: number;
  author: string;
  presenter: string;
  tags: string[];
  last_verified: string;
  saved?: boolean;
}

export interface TrainingMaterial {
  label: string;
  url: string;
}

export interface TrainingDetail extends TrainingSummary {
  session_date: string;
  materials: TrainingMaterial[];
  updated_at: string;
  body_markdown: string;
}

export interface ListTrainingsResult {
  status: string;
  trainings: TrainingSummary[];
  message?: string;
}

export interface GetTrainingResult {
  status: string;
  training?: TrainingDetail;
  message?: string;
}

export interface SaveTrainingResult {
  status: string;
  training_id: string;
  saved: boolean;
  saved_trainings: string[];
  message?: string;
}

export const THEMES = [
  "Foundations",
  "Prompt Engineering",
  "RAG & Retrieval",
  "Agents & Orchestration",
  "AWS & Bedrock",
  "Governance, Risk & Ethics",
  "Delivery & Consulting",
];

export const SOURCES = ["Internal", "Udemy", "YouTube", "LinkedIn Learning"];
export const LEVELS = ["beginner", "intermediate", "advanced"];

export function formatDuration(min: number): string {
  if (!min) return "";
  if (min < 60) return `${min} min`;
  const h = Math.floor(min / 60);
  const m = min % 60;
  return m ? `${h}h ${m}m` : `${h}h`;
}

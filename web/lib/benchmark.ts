// Shared types + constants for the Client Benchmark Comparator (AGENT-21, Module 22).
// Kept out of the "use server" actions file (which may only export async functions).

export const BENCHMARK_AGENT_ID = "AGENT-21";

// JSON serializes the Python int keys (stage 0-5) as strings.
export interface BenchmarkData {
  status: string;
  assessment_id: string;
  client_stage: number;
  industry: string;
  peer_distribution: Record<string, number>;
  typical_use_cases_at_stage: Record<string, string[]>;
  common_next_moves: string[];
  narrative: string;
  markdown: string;
  vault_file_path?: string;
  message?: string;
}

export const STAGES = [0, 1, 2, 3, 4, 5];

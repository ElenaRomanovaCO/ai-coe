"use server";

// Server actions for the Benchmark Comparator. Invoke AGENT-21 in the module-agents
// Lambda. Under (authenticated), so the middleware gates callers. AGENT-21 is
// non-streaming (deterministic distribution + one Haiku narrative).

import { invokeModule } from "@/lib/aws";
import { BENCHMARK_AGENT_ID, type BenchmarkData } from "@/lib/benchmark";

export async function getBenchmark(assessmentId: string): Promise<BenchmarkData> {
  return invokeModule<BenchmarkData>(BENCHMARK_AGENT_ID, {
    op: "get",
    assessment_id: assessmentId,
  });
}

export async function exportBenchmark(assessmentId: string): Promise<BenchmarkData> {
  return invokeModule<BenchmarkData>(BENCHMARK_AGENT_ID, {
    op: "export",
    assessment_id: assessmentId,
  });
}

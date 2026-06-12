import Link from "next/link";
import { notFound } from "next/navigation";
import { BarChart3 } from "lucide-react";

import { BenchmarkExportButton } from "@/components/benchmark/BenchmarkExportButton";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { STAGES } from "@/lib/benchmark";
import { cn } from "@/lib/utils";

import { getBenchmark } from "../actions";

export const dynamic = "force-dynamic";

export default async function BenchmarkPage({
  params,
}: {
  params: Promise<{ assessment_id: string }>;
}) {
  const { assessment_id } = await params;
  const res = await getBenchmark(assessment_id);
  if (res.status !== "ok") {
    notFound();
  }

  const stage = res.client_stage;
  const dist = res.peer_distribution;
  const maxPct = Math.max(...STAGES.map((s) => dist[String(s)] ?? 0), 1);

  return (
    <div className="mx-auto max-w-5xl">
      <nav className="mb-4 text-sm text-neutral-500">
        <Link
          href={`/modules/maturity-assessment/${assessment_id}`}
          className="hover:text-neutral-900"
        >
          Assessment
        </Link>
        <span className="mx-2">/</span>
        <span className="text-neutral-700">Benchmark</span>
      </nav>

      <header className="mb-6">
        <h1 className="flex items-center gap-2 text-2xl font-semibold">
          <BarChart3 className="h-6 w-6 text-indigo-600" />
          Peer Benchmark
        </h1>
        <p className="mt-1 text-sm capitalize text-neutral-500">
          {res.industry.replace(/-/g, " ")} · client at <strong>stage {stage} of 5</strong>
        </p>
      </header>

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
        <Card className="lg:col-span-2">
          <CardHeader>
            <CardTitle className="text-base">Where the client sits vs peers</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <p className="text-sm leading-relaxed text-neutral-700">{res.narrative}</p>
            <div className="space-y-2">
              {STAGES.map((s) => {
                const pct = dist[String(s)] ?? 0;
                const isClient = s === stage;
                return (
                  <div key={s} className="flex items-center gap-3">
                    <span className="w-16 shrink-0 text-xs text-neutral-500">Stage {s}</span>
                    <div className="h-4 flex-1 overflow-hidden rounded bg-neutral-100">
                      <div
                        className={cn("h-full rounded", isClient ? "bg-indigo-600" : "bg-neutral-300")}
                        style={{ width: `${Math.max(2, (pct / maxPct) * 100)}%` }}
                      />
                    </div>
                    <span className="w-10 shrink-0 text-right text-xs tabular-nums text-neutral-500">
                      {pct.toFixed(0)}%
                    </span>
                    {isClient && (
                      <span className="shrink-0 text-[10px] font-medium uppercase text-indigo-600">
                        client
                      </span>
                    )}
                  </div>
                );
              })}
            </div>
          </CardContent>
        </Card>

        <div className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle className="text-base">Common next moves</CardTitle>
            </CardHeader>
            <CardContent>
              <ul className="list-disc space-y-1 pl-5 text-sm text-neutral-700">
                {res.common_next_moves.map((m, i) => (
                  <li key={i}>{m}</li>
                ))}
              </ul>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle className="text-base">Typical at stage {stage}</CardTitle>
            </CardHeader>
            <CardContent>
              <ul className="list-disc space-y-1 pl-5 text-sm text-neutral-700">
                {(res.typical_use_cases_at_stage[String(stage)] ?? []).map((u, i) => (
                  <li key={i}>{u}</li>
                ))}
              </ul>
            </CardContent>
          </Card>

          <BenchmarkExportButton assessmentId={assessment_id} markdown={res.markdown} />
        </div>
      </div>
    </div>
  );
}

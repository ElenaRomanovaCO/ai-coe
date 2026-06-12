import Link from "next/link";
import { notFound } from "next/navigation";
import { AlertTriangle } from "lucide-react";

import { StageIndicator } from "@/components/StageIndicator";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { humanizeDimension } from "@/lib/assessment";

import { getAssessment } from "../actions";

export const dynamic = "force-dynamic";

export default async function AssessmentResultPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = await params;
  const res = await getAssessment(id);

  if (res.status === "not_found") notFound();

  if (!res.is_complete || !res.result) {
    return (
      <div className="mx-auto max-w-3xl">
        <h1 className="text-2xl font-semibold">Assessment in progress</h1>
        <p className="mt-2 text-sm text-slate-500">This assessment hasn&apos;t been completed yet.</p>
        <Link href="/modules/maturity-assessment" className="mt-4 inline-block text-sm text-indigo-600 hover:underline">
          ← Back to assessments
        </Link>
      </div>
    );
  }

  const { stage, rationale, dimension_scores, recommendations } = res.result;
  const dims = Object.entries(dimension_scores);
  const [bindingDim, bindingScore] = dims.reduce(
    (lo, cur) => (cur[1] < lo[1] ? cur : lo),
    dims[0] ?? ["", 0],
  );

  return (
    <div className="mx-auto max-w-5xl">
      <nav className="mb-4 text-sm text-slate-500">
        <Link href="/modules/maturity-assessment" className="hover:text-slate-900">
          AI Maturity Assessment
        </Link>
        <span className="mx-2">/</span>
        <span className="text-slate-700">Result</span>
      </nav>

      <div className="grid gap-6 lg:grid-cols-3">
        {/* Hero stage card */}
        <Card className="lg:col-span-2">
          <CardHeader>
            <CardTitle>Maturity Result</CardTitle>
          </CardHeader>
          <CardContent className="space-y-5">
            <div className="rounded-lg border border-indigo-100 bg-indigo-50/50 p-5">
              <StageIndicator stage={stage} />
            </div>
            <p className="text-sm leading-6 text-slate-700">{rationale}</p>

            {/* Per-dimension bars */}
            <div className="space-y-2">
              <h3 className="text-sm font-semibold text-slate-800">Dimension scores</h3>
              {dims.map(([dim, score]) => (
                <div key={dim} className="flex items-center gap-3">
                  <span className="w-40 shrink-0 text-sm text-slate-600">
                    {humanizeDimension(dim)}
                  </span>
                  <div className="h-2 flex-1 overflow-hidden rounded-full bg-slate-200">
                    <div
                      className="h-full rounded-full bg-indigo-600"
                      style={{ width: `${(score / 5) * 100}%` }}
                    />
                  </div>
                  <span className="w-8 shrink-0 text-right text-sm tabular-nums text-slate-500">
                    {score}/5
                  </span>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>

        {/* Side rail: binding constraint, actions, recommendations */}
        <div className="space-y-6">
          {bindingDim && (
            <Card className="border-amber-200 bg-amber-50/50">
              <CardHeader>
                <CardTitle className="flex items-center gap-2 text-amber-800">
                  <AlertTriangle className="h-4 w-4" /> Binding constraint
                </CardTitle>
              </CardHeader>
              <CardContent className="text-sm text-amber-900">
                <strong>{humanizeDimension(bindingDim)}</strong> ({bindingScore}/5) is the lowest
                dimension — addressing it will move the stage the most.
              </CardContent>
            </Card>
          )}

          <Card>
            <CardHeader>
              <CardTitle>Recommended assets</CardTitle>
            </CardHeader>
            <CardContent>
              {recommendations.length === 0 ? (
                <p className="text-sm text-slate-400">No recommendations available.</p>
              ) : (
                <ul className="space-y-2">
                  {recommendations.map((a) => (
                    <li key={a.id}>
                      <Link
                        href={`/modules/asset-library/${a.id}`}
                        className="flex items-center justify-between gap-2 text-sm hover:underline"
                      >
                        <span className="truncate">{a.title}</span>
                        <span className="shrink-0 rounded bg-slate-100 px-1.5 py-0.5 text-[11px] text-slate-600">
                          {a.type}
                        </span>
                      </Link>
                    </li>
                  ))}
                </ul>
              )}
            </CardContent>
          </Card>

          <Link
            href={`/modules/benchmark/${id}`}
            className="block w-full rounded-md bg-indigo-600 px-3 py-2 text-center text-sm font-medium text-white hover:bg-indigo-700"
          >
            Benchmark vs peers
          </Link>

          <Button
            variant="outline"
            className="w-full"
            disabled
            title="Enabled with the Client Report module (Module 14)"
          >
            Generate client report
          </Button>
        </div>
      </div>
    </div>
  );
}

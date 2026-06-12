"use client";

import { useEffect, useState, useSyncExternalStore } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { FileText } from "lucide-react";

import { StageIndicator } from "@/components/StageIndicator";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import type { AssessmentSummary } from "@/lib/assessment";
import { getDisplayName } from "@/lib/auth";
import type { ReportSummary } from "@/lib/reports";

import { generateReport, listMyAssessments, listReports } from "./actions";

export default function ReportsPage() {
  const router = useRouter();
  const name = useSyncExternalStore(
    () => () => {},
    () => getDisplayName(),
    () => null,
  );

  const [assessments, setAssessments] = useState<AssessmentSummary[]>([]);
  const [reports, setReports] = useState<ReportSummary[]>([]);
  const [loaded, setLoaded] = useState(false);
  const [generatingId, setGeneratingId] = useState<string | null>(null);

  useEffect(() => {
    if (!name) return;
    Promise.all([listMyAssessments(name), listReports(name)])
      .then(([a, r]) => {
        setAssessments((a.assessments ?? []).filter((x) => x.status === "complete"));
        setReports(r.reports ?? []);
      })
      .finally(() => setLoaded(true));
  }, [name]);

  async function onGenerate(assessmentId: string) {
    setGeneratingId(assessmentId);
    try {
      const res = await generateReport(assessmentId);
      if (res.status === "ok") {
        router.push(`/modules/reports/${res.report_id}`);
      } else {
        setGeneratingId(null);
      }
    } catch {
      setGeneratingId(null);
    }
  }

  if (!name) {
    return (
      <div className="mx-auto max-w-3xl">
        <h1 className="text-2xl font-semibold">Client Maturity Report</h1>
        <p className="mt-2 text-sm text-slate-500">
          Set a display name (log out and back in) to generate reports.
        </p>
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-5xl">
      <div className="mb-6">
        <h1 className="flex items-center gap-2 text-2xl font-semibold">
          <FileText className="h-6 w-6 text-indigo-600" />
          Client Maturity Report
        </h1>
        <p className="mt-1 text-sm text-slate-500">
          Turn a completed maturity assessment into a polished, client-ready report. Edit any
          section, then export to PDF for sharing.
        </p>
      </div>

      <div className="grid gap-6 lg:grid-cols-2">
        {/* Generate from a completed assessment */}
        <Card>
          <CardHeader>
            <CardTitle>Generate from an assessment</CardTitle>
          </CardHeader>
          <CardContent>
            {!loaded ? (
              <div className="space-y-2">
                {[0, 1, 2].map((i) => (
                  <div key={i} className="h-12 animate-pulse rounded bg-slate-100" />
                ))}
              </div>
            ) : assessments.length === 0 ? (
              <p className="text-sm text-slate-400">
                No completed assessments yet.{" "}
                <Link
                  href="/modules/maturity-assessment"
                  className="text-indigo-600 hover:underline"
                >
                  Run one first
                </Link>
                .
              </p>
            ) : (
              <ul className="space-y-3">
                {assessments.map((a) => (
                  <li
                    key={a.assessment_id}
                    className="flex items-center justify-between gap-3 rounded-md border border-slate-200 p-3"
                  >
                    <div className="min-w-0">
                      <div className="mb-1 text-xs text-slate-500">
                        {(a.created_at || "").slice(0, 10)}
                      </div>
                      {a.stage !== null ? (
                        <StageIndicator stage={a.stage} size="sm" showLabel />
                      ) : null}
                    </div>
                    <button
                      onClick={() => onGenerate(a.assessment_id)}
                      disabled={generatingId !== null}
                      className="shrink-0 rounded-md bg-indigo-600 px-3 py-1.5 text-sm font-medium text-white hover:bg-indigo-700 disabled:opacity-50"
                    >
                      {generatingId === a.assessment_id ? "Generating…" : "Generate"}
                    </button>
                  </li>
                ))}
              </ul>
            )}
          </CardContent>
        </Card>

        {/* Past reports */}
        <Card>
          <CardHeader>
            <CardTitle>Your reports</CardTitle>
          </CardHeader>
          <CardContent>
            {!loaded ? (
              <div className="space-y-2">
                {[0, 1].map((i) => (
                  <div key={i} className="h-12 animate-pulse rounded bg-slate-100" />
                ))}
              </div>
            ) : reports.length === 0 ? (
              <p className="text-sm text-slate-400">No reports yet.</p>
            ) : (
              <ul className="space-y-3">
                {reports.map((r) => (
                  <li key={r.report_id}>
                    <Link
                      href={`/modules/reports/${r.report_id}`}
                      className="block rounded-md border border-slate-200 p-3 hover:bg-slate-50"
                    >
                      <div className="mb-1 flex items-center justify-between text-xs text-slate-500">
                        <span className="capitalize">{(r.industry || "").replace(/-/g, " ")}</span>
                        <span>{(r.updated_at || r.created_at || "").slice(0, 10)}</span>
                      </div>
                      <div className="truncate text-sm font-medium text-slate-800">{r.title}</div>
                    </Link>
                  </li>
                ))}
              </ul>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}

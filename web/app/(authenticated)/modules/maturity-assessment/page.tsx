"use client";

import { useEffect, useState, useSyncExternalStore } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";

import { AssessmentChat } from "@/components/AssessmentChat";
import { StageIndicator } from "@/components/StageIndicator";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import type { AssessmentResult, AssessmentSummary } from "@/lib/assessment";
import { getDisplayName } from "@/lib/auth";

import { listAssessments, startAssessment } from "./actions";

const DIMENSIONS = [
  "Data Readiness",
  "Org Culture",
  "AI Tooling",
  "Use Case Clarity",
  "Governance",
  "Budget & Sponsorship",
];

export default function MaturityAssessmentPage() {
  const router = useRouter();
  const name = useSyncExternalStore(
    () => () => {},
    () => getDisplayName(),
    () => null,
  );

  const [past, setPast] = useState<AssessmentSummary[]>([]);
  const [loaded, setLoaded] = useState(false);
  const [context, setContext] = useState("");
  const [starting, setStarting] = useState(false);
  const [active, setActive] = useState<{ id: string; question: string } | null>(null);

  useEffect(() => {
    if (!name) return;
    listAssessments(name)
      .then((r) => {
        setPast(r.assessments ?? []);
        setLoaded(true);
      })
      .catch(() => setLoaded(true));
  }, [name]);

  async function onStart() {
    if (!name) return;
    setStarting(true);
    try {
      const res = await startAssessment(name, context || undefined);
      if (res.status === "ok") {
        setActive({ id: res.assessment_id, question: res.next_question });
      }
    } finally {
      setStarting(false);
    }
  }

  function onComplete(result: AssessmentResult) {
    router.push(`/modules/maturity-assessment/${result.assessment_id}`);
  }

  if (!name) {
    return (
      <div className="mx-auto max-w-3xl">
        <h1 className="text-2xl font-semibold">AI Maturity Assessment</h1>
        <p className="mt-2 text-sm text-slate-500">Set a display name (log out and back in) to run an assessment.</p>
      </div>
    );
  }

  // In-progress: the guided conversational flow.
  if (active) {
    return (
      <div className="mx-auto max-w-3xl">
        <h1 className="mb-1 text-2xl font-semibold">AI Maturity Assessment</h1>
        <p className="mb-6 text-sm text-slate-500">
          Answer in your own words — there are no wrong answers. We&apos;ll place the client on a 0–5
          maturity stage and recommend next steps.
        </p>
        <AssessmentChat
          assessmentId={active.id}
          firstQuestion={active.question}
          onComplete={onComplete}
        />
      </div>
    );
  }

  // Intro / empty state.
  return (
    <div className="mx-auto max-w-5xl">
      <div className="mb-6">
        <h1 className="text-2xl font-semibold">AI Maturity Assessment</h1>
        <p className="mt-1 text-sm text-slate-500">
          A guided interview that places an organization on the 0–5 AI maturity curve and recommends
          stage-appropriate next steps.
        </p>
      </div>

      <div className="grid gap-6 lg:grid-cols-3">
        <Card className="lg:col-span-2">
          <CardHeader>
            <CardTitle>Start a new assessment</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <p className="text-sm text-slate-600">
              We&apos;ll ask 8–12 short questions across six dimensions:
            </p>
            <ul className="grid grid-cols-2 gap-2 text-sm text-slate-700">
              {DIMENSIONS.map((d) => (
                <li key={d} className="flex items-center gap-2">
                  <span className="h-1.5 w-1.5 rounded-full bg-indigo-600" />
                  {d}
                </li>
              ))}
            </ul>
            <div>
              <label className="mb-1 block text-sm font-medium text-slate-700">
                Client context <span className="font-normal text-slate-400">(optional)</span>
              </label>
              <Input
                value={context}
                onChange={(e) => setContext(e.target.value)}
                placeholder="e.g. a regional bank exploring fraud detection"
              />
            </div>
            <Button onClick={onStart} disabled={starting} className="bg-indigo-600 hover:bg-indigo-700">
              {starting ? "Starting…" : "Start Assessment"}
            </Button>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Past assessments</CardTitle>
          </CardHeader>
          <CardContent>
            {!loaded ? (
              <div className="space-y-2">
                {[0, 1, 2].map((i) => (
                  <div key={i} className="h-10 animate-pulse rounded bg-slate-100" />
                ))}
              </div>
            ) : past.length === 0 ? (
              <p className="text-sm text-slate-400">No assessments yet.</p>
            ) : (
              <ul className="space-y-3">
                {past.map((a) => (
                  <li key={a.assessment_id}>
                    <Link
                      href={`/modules/maturity-assessment/${a.assessment_id}`}
                      className="block rounded-md border border-slate-200 p-3 hover:bg-slate-50"
                    >
                      <div className="mb-2 flex items-center justify-between text-xs text-slate-500">
                        <span>{(a.created_at || "").slice(0, 10)}</span>
                        <span className="capitalize">{a.status.replace(/_/g, " ")}</span>
                      </div>
                      {a.stage !== null ? (
                        <StageIndicator stage={a.stage} size="sm" showLabel />
                      ) : (
                        <span className="text-xs text-slate-400">In progress</span>
                      )}
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

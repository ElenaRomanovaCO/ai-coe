"use client";

import { useState, useSyncExternalStore, useTransition } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { getDisplayName } from "@/lib/auth";
import { INDUSTRIES, toList } from "@/lib/health";

import { registerEngagement } from "../actions";

export default function NewEngagementPage() {
  const name = useSyncExternalStore(
    () => () => {},
    () => getDisplayName(),
    () => null,
  );

  const router = useRouter();
  const [engName, setEngName] = useState("");
  const [industry, setIndustry] = useState("financial-services");
  const [stage, setStage] = useState(2);
  const [useCases, setUseCases] = useState("");
  const [startDate, setStartDate] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [pending, startTransition] = useTransition();

  function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    if (!engName.trim()) {
      setError("An engagement name is required.");
      return;
    }
    startTransition(async () => {
      const res = await registerEngagement({
        display_name: name ?? "Guest",
        name: engName.trim(),
        industry,
        ai_stage: stage,
        use_cases: toList(useCases),
        start_date: startDate.trim(),
      });
      if (res.status === "ok" && res.engagement?.engagement_id) {
        router.push(`/modules/project-health/${res.engagement.engagement_id}`);
      } else {
        setError(res.message || "Couldn't register the engagement. Please try again.");
      }
    });
  }

  return (
    <div className="mx-auto max-w-3xl">
      <nav className="mb-4 text-sm text-neutral-500">
        <Link href="/modules/project-health" className="hover:text-neutral-900">
          Project Health
        </Link>
        <span className="mx-2">/</span>
        <span className="text-neutral-700">New</span>
      </nav>

      <Card>
        <CardHeader>
          <CardTitle>Register an engagement</CardTitle>
        </CardHeader>
        <CardContent>
          <form onSubmit={onSubmit} className="space-y-4">
            <Field label="Engagement name">
              <Input
                value={engName}
                onChange={(e) => setEngName(e.target.value)}
                placeholder="Fintech RAG Platform"
              />
            </Field>
            <div className="flex gap-3">
              <Field label="Industry">
                <select
                  value={industry}
                  onChange={(e) => setIndustry(e.target.value)}
                  className="flex h-10 w-full rounded-md border border-neutral-300 bg-transparent px-3 text-sm capitalize"
                >
                  {INDUSTRIES.map((i) => (
                    <option key={i} value={i}>
                      {i.replace(/-/g, " ")}
                    </option>
                  ))}
                </select>
              </Field>
              <Field label="AI stage">
                <select
                  value={stage}
                  onChange={(e) => setStage(Number(e.target.value))}
                  className="flex h-10 w-full rounded-md border border-neutral-300 bg-transparent px-3 text-sm"
                >
                  {[0, 1, 2, 3, 4, 5].map((s) => (
                    <option key={s} value={s}>
                      Stage {s}
                    </option>
                  ))}
                </select>
              </Field>
              <Field label="Start date">
                <Input
                  type="date"
                  value={startDate}
                  onChange={(e) => setStartDate(e.target.value)}
                />
              </Field>
            </div>
            <Field label="Use cases" hint="one per line">
              <textarea
                value={useCases}
                onChange={(e) => setUseCases(e.target.value)}
                placeholder={"document Q&A\nfraud triage"}
                rows={3}
                className="w-full rounded-md border border-neutral-300 bg-transparent px-3 py-2 text-sm placeholder:text-neutral-400"
              />
            </Field>

            {error && <p className="text-sm text-red-600">{error}</p>}

            <Button type="submit" disabled={pending} className="bg-indigo-600 hover:bg-indigo-700">
              {pending ? "Registering…" : "Register engagement"}
            </Button>
          </form>
        </CardContent>
      </Card>
    </div>
  );
}

function Field({
  label,
  hint,
  children,
}: {
  label: string;
  hint?: string;
  children: React.ReactNode;
}) {
  return (
    <div className="flex-1">
      <label className="mb-1 block text-sm font-medium text-neutral-700">
        {label}
        {hint && <span className="ml-2 text-xs font-normal text-neutral-400">{hint}</span>}
      </label>
      {children}
    </div>
  );
}

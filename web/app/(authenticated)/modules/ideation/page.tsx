"use client";

import { useState, useSyncExternalStore, useTransition } from "react";
import { useRouter } from "next/navigation";
import { Lightbulb } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { getDisplayName } from "@/lib/auth";
import { AI_STAGES, INDUSTRIES, toList } from "@/lib/ideation";

import { generateIdeation } from "./actions";

export default function IdeationPage() {
  const name = useSyncExternalStore(
    () => () => {},
    () => getDisplayName(),
    () => null,
  );

  const router = useRouter();
  const [industry, setIndustry] = useState("retail");
  const [stage, setStage] = useState(2);
  const [painPoints, setPainPoints] = useState("");
  const [goals, setGoals] = useState("");
  const [availableData, setAvailableData] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [pending, startTransition] = useTransition();

  function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    startTransition(async () => {
      const res = await generateIdeation({
        display_name: name ?? "Guest",
        industry,
        ai_stage: stage,
        pain_points: toList(painPoints),
        goals: toList(goals),
        available_data: toList(availableData),
      });
      if (res.status === "ok" && res.ideation_id) {
        router.push(`/modules/ideation/${res.ideation_id}`);
      } else {
        setError(res.message || "Couldn't generate use cases. Please try again.");
      }
    });
  }

  return (
    <div className="mx-auto max-w-3xl">
      <div className="mb-6">
        <h1 className="flex items-center gap-2 text-2xl font-semibold">
          <Lightbulb className="h-6 w-6 text-indigo-600" />
          Use Case Ideation Engine
        </h1>
        <p className="mt-1 text-sm text-neutral-500">
          Describe the client context and get a ranked set of AI use-case candidates with
          effort/impact, prerequisites, and reference examples.
        </p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Client context</CardTitle>
        </CardHeader>
        <CardContent>
          <form onSubmit={onSubmit} className="space-y-4">
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
              <Field label="AI maturity stage">
                <select
                  value={stage}
                  onChange={(e) => setStage(Number(e.target.value))}
                  className="flex h-10 w-full rounded-md border border-neutral-300 bg-transparent px-3 text-sm"
                >
                  {AI_STAGES.map((s) => (
                    <option key={s} value={s}>
                      Stage {s}
                    </option>
                  ))}
                </select>
              </Field>
            </div>
            <Field label="Pain points" hint="one per line">
              <Textarea
                value={painPoints}
                onChange={setPainPoints}
                placeholder={"high customer churn\nslow manual underwriting"}
              />
            </Field>
            <Field label="Goals" hint="one per line">
              <Textarea
                value={goals}
                onChange={setGoals}
                placeholder={"reduce churn\nspeed up decisions"}
              />
            </Field>
            <Field label="Available data" hint="one per line">
              <Textarea
                value={availableData}
                onChange={setAvailableData}
                placeholder={"customer transactions\nsupport tickets"}
              />
            </Field>

            {error && <p className="text-sm text-red-600">{error}</p>}

            <Button
              type="submit"
              disabled={pending}
              className="bg-indigo-600 hover:bg-indigo-700"
            >
              {pending ? "Generating candidates…" : "Generate use cases"}
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

function Textarea({
  value,
  onChange,
  placeholder,
}: {
  value: string;
  onChange: (v: string) => void;
  placeholder?: string;
}) {
  return (
    <textarea
      value={value}
      onChange={(e) => onChange(e.target.value)}
      placeholder={placeholder}
      rows={3}
      className="w-full rounded-md border border-neutral-300 bg-transparent px-3 py-2 text-sm placeholder:text-neutral-400"
    />
  );
}

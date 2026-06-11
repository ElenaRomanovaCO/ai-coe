"use client";

import { use, useState, useSyncExternalStore, useTransition } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { getDisplayName } from "@/lib/auth";
import { toList } from "@/lib/retros";

import { writeRetro } from "../../actions";

export default function NewRetroPage({
  params,
}: {
  params: Promise<{ engagement_id: string }>;
}) {
  const { engagement_id } = use(params);
  const name = useSyncExternalStore(
    () => () => {},
    () => getDisplayName(),
    () => null,
  );

  const router = useRouter();
  const [useCases, setUseCases] = useState("");
  const [patterns, setPatterns] = useState("");
  const [whatWorked, setWhatWorked] = useState("");
  const [whatFailed, setWhatFailed] = useState("");
  const [toolsRec, setToolsRec] = useState("");
  const [toolsNot, setToolsNot] = useState("");
  const [stage, setStage] = useState(2);
  const [error, setError] = useState<string | null>(null);
  const [pending, startTransition] = useTransition();

  function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    if (!whatWorked.trim() && !whatFailed.trim()) {
      setError("Fill in what worked and/or what failed so insights can be extracted.");
      return;
    }
    startTransition(async () => {
      const res = await writeRetro({
        display_name: name ?? "Guest",
        engagement_id,
        use_cases_attempted: toList(useCases),
        patterns_used: toList(patterns),
        what_worked: whatWorked.trim(),
        what_failed: whatFailed.trim(),
        tools_recommended: toList(toolsRec),
        tools_not_recommended: toList(toolsNot),
        stage_reassessment: stage,
      });
      if (res.status === "ok" && res.retro?.retro_id) {
        router.push(`/modules/retros/${res.retro.retro_id}`);
      } else {
        setError(res.message || "Couldn't save the retro. Please try again.");
      }
    });
  }

  return (
    <div className="mx-auto max-w-3xl">
      <nav className="mb-4 text-sm text-neutral-500">
        <Link href="/modules/retros" className="hover:text-neutral-900">
          Retrospectives
        </Link>
        <span className="mx-2">/</span>
        <span className="text-neutral-700">New · {engagement_id}</span>
      </nav>

      <Card>
        <CardHeader>
          <CardTitle>Engagement retrospective</CardTitle>
        </CardHeader>
        <CardContent>
          <form onSubmit={onSubmit} className="space-y-4">
            <Field label="Use cases attempted" hint="one per line">
              <Area value={useCases} onChange={setUseCases} placeholder={"document Q&A\nfraud triage"} />
            </Field>
            <Field label="Patterns used" hint="asset ids, one per line">
              <Area value={patterns} onChange={setPatterns} placeholder={"solution-pattern-rag-eval"} />
            </Field>
            <Field label="What worked">
              <Area value={whatWorked} onChange={setWhatWorked} />
            </Field>
            <Field label="What failed">
              <Area value={whatFailed} onChange={setWhatFailed} />
            </Field>
            <div className="flex gap-3">
              <Field label="Tools recommended" hint="comma/line">
                <Area value={toolsRec} onChange={setToolsRec} rows={2} />
              </Field>
              <Field label="Tools not recommended" hint="comma/line">
                <Area value={toolsNot} onChange={setToolsNot} rows={2} />
              </Field>
            </div>
            <Field label="Stage reassessment (0–5)">
              <Input
                type="number"
                min={0}
                max={5}
                value={stage}
                onChange={(e) => setStage(Number(e.target.value))}
                className="w-24"
              />
            </Field>

            {error && <p className="text-sm text-red-600">{error}</p>}

            <Button type="submit" disabled={pending} className="bg-indigo-600 hover:bg-indigo-700">
              {pending ? "Extracting insights…" : "Save retro & extract insights"}
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

function Area({
  value,
  onChange,
  placeholder,
  rows = 3,
}: {
  value: string;
  onChange: (v: string) => void;
  placeholder?: string;
  rows?: number;
}) {
  return (
    <textarea
      value={value}
      onChange={(e) => onChange(e.target.value)}
      placeholder={placeholder}
      rows={rows}
      className="w-full rounded-md border border-neutral-300 bg-transparent px-3 py-2 text-sm placeholder:text-neutral-400"
    />
  );
}

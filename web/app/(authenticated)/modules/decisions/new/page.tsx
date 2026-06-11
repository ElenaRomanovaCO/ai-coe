"use client";

import { useState, useSyncExternalStore, useTransition } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { getDisplayName } from "@/lib/auth";
import { toList } from "@/lib/decisions";

import { writeDecision } from "../actions";

export default function NewDecisionPage() {
  const name = useSyncExternalStore(
    () => () => {},
    () => getDisplayName(),
    () => null,
  );

  const router = useRouter();
  const [decision, setDecision] = useState("");
  const [context, setContext] = useState("");
  const [alternatives, setAlternatives] = useState("");
  const [rationale, setRationale] = useState("");
  const [outcome, setOutcome] = useState("");
  const [tags, setTags] = useState("");
  const [engagementId, setEngagementId] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [pending, startTransition] = useTransition();

  function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    if (!decision.trim()) {
      setError("A decision statement is required.");
      return;
    }
    startTransition(async () => {
      const res = await writeDecision({
        display_name: name ?? "Guest",
        decision: decision.trim(),
        context: context.trim(),
        alternatives: toList(alternatives),
        rationale: rationale.trim(),
        outcome: outcome.trim() || null,
        tags: toList(tags),
        engagement_id: engagementId.trim() || null,
      });
      if (res.status === "ok" && res.decision?.decision_id) {
        router.push(`/modules/decisions/${res.decision.decision_id}`);
      } else {
        setError(res.message || "Couldn't save the decision. Please try again.");
      }
    });
  }

  return (
    <div className="mx-auto max-w-3xl">
      <nav className="mb-4 text-sm text-neutral-500">
        <Link href="/modules/decisions" className="hover:text-neutral-900">
          Decision Log
        </Link>
        <span className="mx-2">/</span>
        <span className="text-neutral-700">New</span>
      </nav>

      <Card>
        <CardHeader>
          <CardTitle>Log a decision</CardTitle>
        </CardHeader>
        <CardContent>
          <form onSubmit={onSubmit} className="space-y-4">
            <Field label="Decision" hint="what was decided">
              <Input
                value={decision}
                onChange={(e) => setDecision(e.target.value)}
                placeholder="Use a managed vector store for clinical-notes RAG"
              />
            </Field>
            <Field label="Context" hint="the situation / constraint">
              <Textarea value={context} onChange={setContext} />
            </Field>
            <Field label="Alternatives considered" hint="one per line">
              <Textarea
                value={alternatives}
                onChange={setAlternatives}
                placeholder={"self-hosted pgvector\nElasticsearch kNN"}
              />
            </Field>
            <Field label="Rationale" hint="why this choice">
              <Textarea value={rationale} onChange={setRationale} />
            </Field>
            <div className="flex gap-3">
              <Field label="Outcome (optional)" hint="fill in later">
                <Input value={outcome} onChange={(e) => setOutcome(e.target.value)} />
              </Field>
              <Field label="Engagement ID (optional)">
                <Input value={engagementId} onChange={(e) => setEngagementId(e.target.value)} />
              </Field>
            </div>
            <Field label="Tags" hint="comma-separated · more auto-suggested on save">
              <Input
                value={tags}
                onChange={(e) => setTags(e.target.value)}
                placeholder="healthcare, vector-db"
              />
            </Field>

            {error && <p className="text-sm text-red-600">{error}</p>}

            <Button type="submit" disabled={pending} className="bg-indigo-600 hover:bg-indigo-700">
              {pending ? "Saving…" : "Save decision"}
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

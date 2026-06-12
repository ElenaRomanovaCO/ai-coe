"use client";

import { useState, useSyncExternalStore } from "react";
import Link from "next/link";
import { AlertTriangle, CheckCircle2, FilePlus2, Loader2 } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { getDisplayName } from "@/lib/auth";
import { ASSET_TYPES, INDUSTRIES, type PendingRecord } from "@/lib/contribute";

import { submitAsset } from "./actions";

const STAGES = [0, 1, 2, 3, 4, 5];

export default function ContributePage() {
  const name = useSyncExternalStore(
    () => () => {},
    () => getDisplayName(),
    () => null,
  );

  const [title, setTitle] = useState("");
  const [type, setType] = useState(ASSET_TYPES[1]);
  const [industry, setIndustry] = useState(INDUSTRIES[8]);
  const [stage, setStage] = useState(2);
  const [body, setBody] = useState("");
  const [notes, setNotes] = useState("");
  const [busy, setBusy] = useState(false);
  const [result, setResult] = useState<PendingRecord | null>(null);

  async function onSubmit() {
    if (!name || !title.trim() || !body.trim()) return;
    setBusy(true);
    try {
      const res = await submitAsset({
        display_name: name,
        title: title.trim(),
        type,
        industry,
        ai_stage: stage,
        body_markdown: body,
        contributor_notes: notes.trim() || undefined,
      });
      if (res.status === "ok") setResult(res);
    } finally {
      setBusy(false);
    }
  }

  if (!name) {
    return (
      <div className="mx-auto max-w-3xl">
        <h1 className="text-2xl font-semibold">Contribute Knowledge</h1>
        <p className="mt-2 text-sm text-slate-500">
          Set a display name (log out and back in) to contribute.
        </p>
      </div>
    );
  }

  if (result) {
    const flags = result.anonymization?.flagged_spans ?? [];
    const dups = result.tag_suggestions?.duplicates ?? [];
    return (
      <div className="mx-auto max-w-3xl">
        <div className="mb-6 flex items-center gap-2 rounded-lg border border-green-200 bg-green-50 p-4 text-sm text-green-800">
          <CheckCircle2 className="h-5 w-5 shrink-0" />
          Submitted for curator review. Our AI assistant analyzed it before queueing.
        </div>

        <Card className="mb-4">
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-base">
              <AlertTriangle className="h-4 w-4 text-amber-500" />
              Anonymization — {flags.length} potential identifier{flags.length === 1 ? "" : "s"}
            </CardTitle>
          </CardHeader>
          <CardContent>
            {flags.length === 0 ? (
              <p className="text-sm text-slate-500">No identifying details flagged.</p>
            ) : (
              <ul className="space-y-2 text-sm">
                {flags.map((f, i) => (
                  <li key={i} className="rounded border border-amber-100 bg-amber-50/50 p-2">
                    <span className="font-medium text-amber-900">&ldquo;{f.span}&rdquo;</span>
                    <span className="text-slate-500"> → </span>
                    <span className="text-slate-700">{f.suggested_replacement}</span>
                    <div className="text-xs text-slate-400">{f.reason}</div>
                  </li>
                ))}
              </ul>
            )}
          </CardContent>
        </Card>

        <Card className="mb-6">
          <CardHeader>
            <CardTitle className="text-base">
              Suggested tags &amp; {dups.length} possible duplicate{dups.length === 1 ? "" : "s"}
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            <div className="flex flex-wrap gap-1.5">
              {(result.tag_suggestions?.tags ?? []).map((t) => (
                <span key={t} className="rounded bg-indigo-50 px-2 py-0.5 text-xs text-indigo-700">
                  {t}
                </span>
              ))}
            </div>
            {dups.length > 0 && (
              <ul className="text-sm text-slate-600">
                {dups.map((d) => (
                  <li key={d.id}>· {d.title}</li>
                ))}
              </ul>
            )}
          </CardContent>
        </Card>

        <div className="flex gap-3">
          <Link href={`/modules/contribute/${result.pending_id}`}>
            <Button>Open in curator review</Button>
          </Link>
          <Link href="/modules/contribute/pending">
            <Button variant="outline">View queue</Button>
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-3xl">
      <div className="mb-6">
        <h1 className="flex items-center gap-2 text-2xl font-semibold">
          <FilePlus2 className="h-6 w-6 text-indigo-600" />
          Contribute Knowledge
        </h1>
        <p className="mt-1 text-sm text-slate-500">
          Share a case study, pattern, or lesson learned. Our AI assistant flags identifying
          details and suggests tags before a curator reviews it.
        </p>
      </div>

      <Card>
        <CardContent className="space-y-4 pt-6">
          <Field label="Title">
            <Input value={title} onChange={(e) => setTitle(e.target.value)} placeholder="e.g. Clinical notes RAG — lessons learned" />
          </Field>
          <div className="grid gap-4 sm:grid-cols-3">
            <Field label="Type">
              <Select value={type} onChange={setType} options={ASSET_TYPES} />
            </Field>
            <Field label="Industry">
              <Select value={industry} onChange={setIndustry} options={INDUSTRIES} />
            </Field>
            <Field label="AI stage">
              <Select
                value={String(stage)}
                onChange={(v) => setStage(Number(v))}
                options={STAGES.map(String)}
              />
            </Field>
          </div>
          <Field label="Body (markdown)">
            <textarea
              value={body}
              onChange={(e) => setBody(e.target.value)}
              rows={12}
              placeholder="Write the asset content here…"
              className="w-full resize-y rounded-md border border-slate-200 px-3 py-2 text-sm text-slate-700 focus:border-indigo-400 focus:outline-none focus:ring-1 focus:ring-indigo-400"
            />
          </Field>
          <Field label="Contributor notes (optional)">
            <Input value={notes} onChange={(e) => setNotes(e.target.value)} placeholder="Anything the curator should know" />
          </Field>
          <Button onClick={onSubmit} disabled={busy || !title.trim() || !body.trim()}>
            {busy ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : null}
            Submit for review
          </Button>
        </CardContent>
      </Card>
    </div>
  );
}

function Field({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div>
      <label className="mb-1 block text-sm font-medium text-slate-700">{label}</label>
      {children}
    </div>
  );
}

function Select({
  value,
  onChange,
  options,
}: {
  value: string;
  onChange: (v: string) => void;
  options: string[];
}) {
  return (
    <select
      value={value}
      onChange={(e) => onChange(e.target.value)}
      className="w-full rounded-md border border-slate-200 px-2 py-2 text-sm text-slate-700 focus:border-indigo-400 focus:outline-none"
    >
      {options.map((o) => (
        <option key={o} value={o}>
          {o}
        </option>
      ))}
    </select>
  );
}

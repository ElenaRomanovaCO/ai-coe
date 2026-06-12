"use client";

import { useState } from "react";
import Link from "next/link";
import { AlertTriangle, CheckCircle2, Loader2, X } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { ASSET_TYPES, INDUSTRIES, type PendingRecord } from "@/lib/contribute";

import { approveAsset, rejectAsset } from "@/app/(authenticated)/modules/contribute/actions";

const STAGES = [0, 1, 2, 3, 4, 5];

function slug(s: string): string {
  return s
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-+|-+$/g, "");
}

export function ContributeReview({ record }: { record: PendingRecord }) {
  const anon = record.anonymization ?? { flagged_spans: [], suggested_anonymized_body: "" };
  const sugg = record.tag_suggestions ?? { tags: [], duplicates: [] };

  const [body, setBody] = useState(anon.suggested_anonymized_body || record.body_markdown);
  const [id, setId] = useState(slug(record.title));
  const [title, setTitle] = useState(record.title);
  const [type, setType] = useState(record.type || ASSET_TYPES[1]);
  const [industry, setIndustry] = useState(record.industry || INDUSTRIES[8]);
  const [stage, setStage] = useState(record.ai_stage ?? 2);
  const [tags, setTags] = useState<string[]>(sugg.tags ?? []);
  const [tagInput, setTagInput] = useState("");
  const [busy, setBusy] = useState<"approve" | "reject" | null>(null);
  const [done, setDone] = useState<{ kind: "approved" | "rejected"; assetId?: string } | null>(
    record.review_status === "approved"
      ? { kind: "approved", assetId: record.approved?.asset_id }
      : record.review_status === "rejected"
        ? { kind: "rejected" }
        : null,
  );

  function addTag(t: string) {
    const v = t.trim().toLowerCase();
    if (v && !tags.includes(v)) setTags([...tags, v]);
    setTagInput("");
  }

  async function onApprove() {
    setBusy("approve");
    try {
      const res = await approveAsset(
        record.pending_id,
        { id, title, type, industry, ai_stage: stage, tags, use_case_type: [] },
        body,
      );
      if (res.status === "ok") setDone({ kind: "approved", assetId: res.asset_id });
    } finally {
      setBusy(null);
    }
  }

  async function onReject() {
    setBusy("reject");
    try {
      const res = await rejectAsset(record.pending_id, "Rejected by curator");
      if (res.status === "ok") setDone({ kind: "rejected" });
    } finally {
      setBusy(null);
    }
  }

  if (done) {
    return (
      <div
        className={
          done.kind === "approved"
            ? "rounded-lg border border-green-200 bg-green-50 p-6"
            : "rounded-lg border border-slate-200 bg-slate-50 p-6"
        }
      >
        <div className="mb-3 flex items-center gap-2 text-lg font-semibold">
          {done.kind === "approved" ? (
            <CheckCircle2 className="h-5 w-5 text-green-600" />
          ) : (
            <X className="h-5 w-5 text-slate-500" />
          )}
          {done.kind === "approved" ? "Approved & published" : "Submission rejected"}
        </div>
        {done.kind === "approved" ? (
          <p className="text-sm text-green-800">
            The asset is now in the library and will be searchable shortly.{" "}
            {done.assetId && (
              <Link
                href={`/modules/asset-library/${done.assetId}`}
                className="font-medium underline"
              >
                View asset
              </Link>
            )}
          </p>
        ) : (
          <p className="text-sm text-slate-600">This submission won&apos;t be published.</p>
        )}
        <Link href="/modules/contribute/pending" className="mt-4 inline-block text-sm text-indigo-600 hover:underline">
          ← Back to queue
        </Link>
      </div>
    );
  }

  return (
    <div>
      <div className="mb-4 flex items-center justify-between gap-3">
        <h1 className="text-2xl font-semibold">Review: {record.title}</h1>
        <span className="text-xs text-slate-500">by {record.display_name}</span>
      </div>

      <div className="flex flex-col gap-8 lg:flex-row">
        {/* Left: anonymized body + flagged spans */}
        <div className="min-w-0 flex-1 space-y-4">
          <div>
            <label className="mb-1 block text-sm font-semibold text-slate-800">
              Anonymized body
            </label>
            <textarea
              value={body}
              onChange={(e) => setBody(e.target.value)}
              rows={18}
              className="w-full resize-y rounded-md border border-slate-200 px-3 py-2 font-mono text-xs text-slate-700 focus:border-indigo-400 focus:outline-none"
            />
          </div>
          <div className="rounded-lg border border-amber-200 bg-amber-50/50 p-4">
            <h3 className="mb-2 flex items-center gap-2 text-sm font-semibold text-amber-900">
              <AlertTriangle className="h-4 w-4" />
              Flagged identifiers ({anon.flagged_spans.length})
            </h3>
            {anon.flagged_spans.length === 0 ? (
              <p className="text-sm text-slate-500">Nothing flagged.</p>
            ) : (
              <ul className="space-y-2 text-sm">
                {anon.flagged_spans.map((f, i) => (
                  <li key={i}>
                    <span className="font-medium text-amber-900">&ldquo;{f.span}&rdquo;</span>
                    <span className="text-slate-500"> → </span>
                    <span className="text-slate-700">{f.suggested_replacement}</span>
                    <div className="text-xs text-slate-400">{f.reason}</div>
                  </li>
                ))}
              </ul>
            )}
          </div>
        </div>

        {/* Right: frontmatter + tags + duplicates + actions */}
        <aside className="w-full shrink-0 space-y-4 lg:w-80">
          <Field label="Asset id">
            <Input value={id} onChange={(e) => setId(e.target.value)} />
          </Field>
          <Field label="Title">
            <Input value={title} onChange={(e) => setTitle(e.target.value)} />
          </Field>
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

          <Field label="Tags">
            <div className="mb-2 flex flex-wrap gap-1.5">
              {tags.map((t) => (
                <span
                  key={t}
                  className="inline-flex items-center gap-1 rounded bg-indigo-50 px-2 py-0.5 text-xs text-indigo-700"
                >
                  {t}
                  <button onClick={() => setTags(tags.filter((x) => x !== t))}>
                    <X className="h-3 w-3" />
                  </button>
                </span>
              ))}
            </div>
            <Input
              value={tagInput}
              onChange={(e) => setTagInput(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === "Enter") {
                  e.preventDefault();
                  addTag(tagInput);
                }
              }}
              placeholder="Add a tag, press Enter"
            />
          </Field>

          {sugg.duplicates.length > 0 && (
            <div className="rounded-lg border border-slate-200 p-3">
              <h3 className="mb-1 text-xs font-semibold uppercase tracking-wide text-slate-500">
                Possible duplicates
              </h3>
              <ul className="text-sm text-slate-600">
                {sugg.duplicates.map((d) => (
                  <li key={d.id} className="truncate">
                    · {d.title}
                  </li>
                ))}
              </ul>
            </div>
          )}

          <div className="flex gap-2 pt-2">
            <Button onClick={onApprove} disabled={busy !== null || !id.trim()} className="flex-1">
              {busy === "approve" ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : null}
              Approve
            </Button>
            <Button onClick={onReject} disabled={busy !== null} variant="outline">
              {busy === "reject" ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : null}
              Reject
            </Button>
          </div>
        </aside>
      </div>
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

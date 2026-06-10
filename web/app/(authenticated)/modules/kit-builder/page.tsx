"use client";

import { useState, useSyncExternalStore } from "react";
import { Plus } from "lucide-react";

import { KitPreview } from "@/components/KitPreview";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { getDisplayName } from "@/lib/auth";
import {
  ENGAGEMENT_TYPES,
  type KitFile,
  type VaultFile,
  categoryForContentType,
} from "@/lib/kit";

import { generateKit, previewKit, searchVault, type KitCriteria } from "./actions";

export default function KitBuilderPage() {
  const name = useSyncExternalStore(
    () => () => {},
    () => getDisplayName(),
    () => null,
  );

  const [industry, setIndustry] = useState("healthcare");
  const [stage, setStage] = useState(2);
  const [engagement, setEngagement] = useState<string>("discovery");
  const [weeks, setWeeks] = useState(6);
  const [context, setContext] = useState("");

  const [kitFiles, setKitFiles] = useState<KitFile[]>([]);
  const [kitSlug, setKitSlug] = useState("");
  const [suggestions, setSuggestions] = useState<VaultFile[]>([]);
  const [busy, setBusy] = useState(false);
  const [generating, setGenerating] = useState(false);
  const [downloadUrl, setDownloadUrl] = useState<string | null>(null);

  function criteria(): KitCriteria {
    return {
      display_name: name ?? "Guest",
      industry,
      ai_stage: stage,
      engagement_type: engagement,
      duration_weeks: weeks,
      extra_context: context || undefined,
    };
  }

  async function onGetSuggestions() {
    setBusy(true);
    setDownloadUrl(null);
    try {
      const manifest = await previewKit(criteria());
      setKitFiles(manifest.files ?? []);
      setKitSlug(manifest.kit_slug ?? "");
      const inKit = new Set((manifest.files ?? []).map((f) => f.source_path));
      const found = await searchVault("", undefined, 20);
      setSuggestions((found.files ?? []).filter((f) => !inKit.has(f.source_path)));
    } finally {
      setBusy(false);
    }
  }

  function addToKit(v: VaultFile) {
    const category = categoryForContentType(v.content_type);
    const base = v.source_path.split("/").pop() ?? v.source_path;
    setKitFiles((k) => [
      ...k,
      {
        category,
        source_path: v.source_path,
        target_path: `${kitSlug}/${category}/${base}`,
        title: v.title,
        rationale: "",
      },
    ]);
    setSuggestions((s) => s.filter((f) => f.source_path !== v.source_path));
    setDownloadUrl(null);
  }

  function removeFromKit(sourcePath: string) {
    setKitFiles((k) => k.filter((f) => f.source_path !== sourcePath));
    setDownloadUrl(null);
  }

  async function onExport() {
    setGenerating(true);
    try {
      const manifest = await generateKit(
        criteria(),
        kitFiles.map((f) => ({ category: f.category, source_path: f.source_path })),
      );
      setDownloadUrl(manifest.download_url ?? null);
    } finally {
      setGenerating(false);
    }
  }

  if (!name) {
    return (
      <div className="mx-auto max-w-3xl">
        <h1 className="text-2xl font-semibold">Engagement Kit Builder</h1>
        <p className="mt-2 text-sm text-slate-500">Set a display name (log out and back in) to build a kit.</p>
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-6xl">
      <div className="mb-6">
        <h1 className="text-2xl font-semibold">Engagement Kit Builder</h1>
        <p className="mt-1 text-sm text-slate-500">
          Describe the engagement, then assemble a tailored starter pack of vault files to export.
        </p>
      </div>

      <div className="grid gap-6 lg:grid-cols-2">
        {/* Left: context + suggestions */}
        <div className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>Engagement context</CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              <Field label="Industry">
                <Input value={industry} onChange={(e) => setIndustry(e.target.value)} />
              </Field>
              <div className="flex gap-3">
                <Field label="AI stage (0–5)">
                  <Input
                    type="number"
                    min={0}
                    max={5}
                    value={stage}
                    onChange={(e) => setStage(Number(e.target.value))}
                  />
                </Field>
                <Field label="Duration (weeks)">
                  <Input
                    type="number"
                    min={1}
                    value={weeks}
                    onChange={(e) => setWeeks(Number(e.target.value))}
                  />
                </Field>
              </div>
              <Field label="Engagement type">
                <select
                  value={engagement}
                  onChange={(e) => setEngagement(e.target.value)}
                  className="flex h-10 w-full rounded-md border border-slate-300 bg-transparent px-3 text-sm"
                >
                  {ENGAGEMENT_TYPES.map((t) => (
                    <option key={t} value={t}>
                      {t}
                    </option>
                  ))}
                </select>
              </Field>
              <Field label="Extra context (optional)">
                <Input
                  value={context}
                  onChange={(e) => setContext(e.target.value)}
                  placeholder="e.g. fraud-scoring pilot starting next month"
                />
              </Field>
              <Button
                onClick={onGetSuggestions}
                disabled={busy}
                className="bg-indigo-600 hover:bg-indigo-700"
              >
                {busy ? "Assembling…" : "Get suggestions"}
              </Button>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Suggestions</CardTitle>
            </CardHeader>
            <CardContent>
              {suggestions.length === 0 ? (
                <p className="text-sm text-slate-400">
                  Get suggestions to see more vault files you can add.
                </p>
              ) : (
                <ul className="space-y-1">
                  {suggestions.map((v) => (
                    <li
                      key={v.source_path}
                      className="flex items-center justify-between gap-2 rounded-md border border-slate-200 px-2.5 py-1.5"
                    >
                      <span className="min-w-0">
                        <span className="block truncate text-sm text-slate-700">{v.title}</span>
                        <span className="text-[11px] text-slate-400">{v.content_type}</span>
                      </span>
                      <button
                        onClick={() => addToKit(v)}
                        aria-label={`Add ${v.title}`}
                        className="shrink-0 text-indigo-600 hover:text-indigo-800"
                      >
                        <Plus className="h-4 w-4" />
                      </button>
                    </li>
                  ))}
                </ul>
              )}
            </CardContent>
          </Card>
        </div>

        {/* Right: kit canvas */}
        <KitPreview
          kitSlug={kitSlug}
          files={kitFiles}
          onRemove={removeFromKit}
          onExport={onExport}
          generating={generating}
          downloadUrl={downloadUrl}
        />
      </div>
    </div>
  );
}

function Field({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div className="flex-1">
      <label className="mb-1 block text-sm font-medium text-slate-700">{label}</label>
      {children}
    </div>
  );
}

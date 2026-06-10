"use client";

import { useMemo, useState, useSyncExternalStore } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { GitBranch, Lightbulb, Save } from "lucide-react";

import {
  savePrompt,
  suggestImprovements,
} from "@/app/(authenticated)/modules/prompt-studio/actions";
import { PromptRunner } from "@/components/PromptRunner";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { getDisplayName } from "@/lib/auth";
import type { PromptDetail, PromptSummary, SuggestResult } from "@/lib/prompts";
import { cn } from "@/lib/utils";

const FIELD_CLASS =
  "w-full rounded-md border border-neutral-300 bg-white px-3 py-2 text-sm text-neutral-900 focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500";

function parseList(s: string): string[] {
  return s
    .split(",")
    .map((x) => x.trim())
    .filter(Boolean);
}

export function PromptEditor({
  prompt,
  history,
}: {
  prompt: PromptDetail;
  history: PromptSummary[];
}) {
  const router = useRouter();
  const name = useSyncExternalStore(
    () => () => {},
    () => getDisplayName(),
    () => null,
  );

  const [title, setTitle] = useState(prompt.title);
  const [useCase, setUseCase] = useState(prompt.use_case);
  const [modelTargets, setModelTargets] = useState((prompt.model_targets ?? []).join(", "));
  const [variables, setVariables] = useState((prompt.variables ?? []).join(", "));
  const [promptText, setPromptText] = useState(prompt.prompt_text);

  const [saving, setSaving] = useState<"version" | "fork" | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [suggesting, setSuggesting] = useState(false);
  const [suggestions, setSuggestions] = useState<SuggestResult | null>(null);

  const variableNames = useMemo(() => parseList(variables), [variables]);

  async function onSave(mode: "version" | "fork") {
    if (!name || saving) return;
    setSaving(mode);
    setError(null);
    try {
      const res = await savePrompt({
        mode,
        source_id: prompt.id,
        title,
        use_case: useCase,
        model_targets: parseList(modelTargets),
        variables: variableNames,
        prompt_text: promptText,
        display_name: name,
      });
      if (res.status === "ok" && res.prompt?.id) {
        router.push(`/modules/prompt-studio/${res.prompt.id}`);
      } else {
        setError(res.message || "Could not save the prompt.");
        setSaving(null);
      }
    } catch {
      setError("Something went wrong saving. Please try again.");
      setSaving(null);
    }
  }

  async function onSuggest() {
    if (suggesting) return;
    setSuggesting(true);
    try {
      const res = await suggestImprovements({
        prompt_text: promptText,
        variables: variableNames,
      });
      setSuggestions(res.status === "ok" ? res : null);
    } catch {
      setSuggestions(null);
    } finally {
      setSuggesting(false);
    }
  }

  return (
    <div className="flex flex-col gap-6 lg:flex-row">
      {/* Editor column */}
      <div className="min-w-0 flex-1 space-y-4">
        <div className="grid gap-3 sm:grid-cols-2">
          <div className="sm:col-span-2">
            <label className="mb-1 block text-xs font-medium text-neutral-600">Title</label>
            <Input value={title} onChange={(e) => setTitle(e.target.value)} />
          </div>
          <div className="sm:col-span-2">
            <label className="mb-1 block text-xs font-medium text-neutral-600">Use case</label>
            <Input value={useCase} onChange={(e) => setUseCase(e.target.value)} />
          </div>
          <div>
            <label className="mb-1 block text-xs font-medium text-neutral-600">
              Model targets <span className="text-neutral-400">(comma-sep)</span>
            </label>
            <Input value={modelTargets} onChange={(e) => setModelTargets(e.target.value)} />
          </div>
          <div>
            <label className="mb-1 block text-xs font-medium text-neutral-600">
              Variables <span className="text-neutral-400">(comma-sep)</span>
            </label>
            <Input value={variables} onChange={(e) => setVariables(e.target.value)} />
          </div>
        </div>

        <div>
          <label className="mb-1 block text-xs font-medium text-neutral-600">Prompt</label>
          <textarea
            className={cn(FIELD_CLASS, "min-h-72 resize-y font-mono text-[13px] leading-relaxed")}
            value={promptText}
            onChange={(e) => setPromptText(e.target.value)}
            placeholder="Write the prompt. Use {{variable}} placeholders."
          />
        </div>

        {error && <p className="text-sm text-red-600">{error}</p>}
        {!name && (
          <p className="text-sm text-neutral-500">
            Set a display name (log out and back in) to save prompts.
          </p>
        )}

        <div className="flex flex-wrap gap-2">
          <Button onClick={() => onSave("version")} disabled={!name || saving !== null}>
            <Save className="h-4 w-4" />
            {saving === "version" ? "Saving…" : "Save as new version"}
          </Button>
          <Button variant="outline" onClick={() => onSave("fork")} disabled={!name || saving !== null}>
            <GitBranch className="h-4 w-4" />
            {saving === "fork" ? "Forking…" : "Save as fork"}
          </Button>
          <Button variant="ghost" onClick={onSuggest} disabled={suggesting}>
            <Lightbulb className="h-4 w-4" />
            {suggesting ? "Analyzing…" : "Suggest improvements"}
          </Button>
        </div>

        {suggestions && <Suggestions result={suggestions} />}
      </div>

      {/* Runner + history column */}
      <aside className="w-full shrink-0 space-y-6 lg:w-96">
        <section className="rounded-lg border border-neutral-200 p-4">
          <h2 className="mb-3 text-sm font-semibold">Run</h2>
          <PromptRunner
            promptId={prompt.id}
            promptText={promptText}
            variableNames={variableNames}
            defaultModel={prompt.model_targets?.[0] ?? "sonnet-4-6"}
          />
        </section>

        {history.length > 1 && (
          <section className="rounded-lg border border-neutral-200 p-4">
            <h2 className="mb-3 text-sm font-semibold">Version history</h2>
            <ul className="space-y-2 text-sm">
              {history.map((v) => (
                <li key={v.id} className="flex items-center justify-between gap-2">
                  <Link
                    href={`/modules/prompt-studio/${v.id}`}
                    className={cn(
                      "min-w-0 flex-1 truncate",
                      v.id === prompt.id ? "font-medium text-indigo-700" : "hover:text-neutral-900",
                    )}
                  >
                    v{v.version} · {v.title}
                  </Link>
                  {v.id !== prompt.id && (
                    <Link
                      href={`/modules/prompt-studio/${prompt.id}/diff/${v.id}`}
                      className="shrink-0 text-xs text-neutral-400 hover:text-indigo-600"
                    >
                      diff
                    </Link>
                  )}
                </li>
              ))}
            </ul>
          </section>
        )}
      </aside>
    </div>
  );
}

function Suggestions({ result }: { result: SuggestResult }) {
  return (
    <div className="space-y-3 rounded-lg border border-amber-200 bg-amber-50 p-4">
      {result.anti_patterns.length > 0 && (
        <div>
          <h3 className="mb-1 text-xs font-semibold uppercase tracking-wide text-amber-700">
            Anti-patterns
          </h3>
          <ul className="space-y-1 text-sm text-neutral-700">
            {result.anti_patterns.map((a) => (
              <li key={a.flag}>
                <span className="font-medium">{a.flag.replace(/-/g, " ")}:</span> {a.detail}
              </li>
            ))}
          </ul>
        </div>
      )}
      <div>
        <h3 className="mb-1 text-xs font-semibold uppercase tracking-wide text-amber-700">
          Suggestions
        </h3>
        <ul className="list-disc space-y-1 pl-5 text-sm text-neutral-700">
          {result.suggestions.map((s, i) => (
            <li key={i}>{s}</li>
          ))}
        </ul>
      </div>
    </div>
  );
}

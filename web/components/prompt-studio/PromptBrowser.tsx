"use client";

import { useMemo, useState } from "react";
import Link from "next/link";
import { Sparkles } from "lucide-react";

import { Input } from "@/components/ui/input";
import type { PromptSummary } from "@/lib/prompts";
import { cn } from "@/lib/utils";

// Client-side filtering over the prompt corpus (seed + user). Model-target facet is
// derived from the data; the text box matches title/use_case.
export function PromptBrowser({ prompts }: { prompts: PromptSummary[] }) {
  const [model, setModel] = useState<string | null>(null);
  const [source, setSource] = useState<string | null>(null);
  const [text, setText] = useState("");

  const models = useMemo(
    () => [...new Set(prompts.flatMap((p) => p.model_targets))].filter(Boolean).sort(),
    [prompts],
  );

  const filtered = useMemo(() => {
    const q = text.trim().toLowerCase();
    return prompts.filter((p) => {
      if (model && !p.model_targets.includes(model)) return false;
      if (source && p.source !== source) return false;
      if (q && !`${p.title} ${p.use_case}`.toLowerCase().includes(q)) return false;
      return true;
    });
  }, [prompts, model, source, text]);

  return (
    <div className="flex gap-6">
      <aside className="w-56 shrink-0 space-y-5 text-sm">
        <Input
          placeholder="Search prompts…"
          value={text}
          onChange={(e) => setText(e.target.value)}
        />
        <FilterGroup
          title="Source"
          options={["seed", "user"]}
          selected={source}
          onSelect={setSource}
        />
        <FilterGroup title="Model target" options={models} selected={model} onSelect={setModel} />
      </aside>

      <div className="flex-1">
        <p className="mb-3 text-sm text-neutral-500">
          {filtered.length} of {prompts.length} prompts
        </p>
        {filtered.length === 0 ? (
          <p className="mt-12 text-center text-neutral-400">No prompts match those filters.</p>
        ) : (
          <ul className="space-y-3">
            {filtered.map((p) => (
              <PromptCard key={p.id} prompt={p} />
            ))}
          </ul>
        )}
      </div>
    </div>
  );
}

function PromptCard({ prompt: p }: { prompt: PromptSummary }) {
  return (
    <li>
      <Link
        href={`/modules/prompt-studio/${p.id}`}
        className="block rounded-lg border border-neutral-200 p-4 transition-colors hover:border-indigo-300 hover:bg-neutral-50"
      >
        <div className="flex items-start gap-3">
          <Sparkles className="mt-0.5 h-5 w-5 shrink-0 text-neutral-400" />
          <div className="min-w-0 flex-1">
            <div className="mb-1 flex flex-wrap items-center gap-2">
              <span
                className={cn(
                  "rounded px-1.5 py-0.5 text-[10px] font-medium uppercase",
                  p.source === "seed"
                    ? "bg-neutral-100 text-neutral-600"
                    : "bg-indigo-100 text-indigo-700",
                )}
              >
                {p.source}
              </span>
              <span className="rounded bg-neutral-100 px-1.5 py-0.5 text-[11px] text-neutral-600">
                v{p.version}
              </span>
              {p.model_targets.map((m) => (
                <span key={m} className="text-[11px] text-neutral-400">
                  {m}
                </span>
              ))}
            </div>
            <p className="text-sm font-medium text-neutral-900">{p.title}</p>
            {p.use_case && <p className="mt-0.5 truncate text-xs text-neutral-500">{p.use_case}</p>}
          </div>
        </div>
      </Link>
    </li>
  );
}

function FilterGroup({
  title,
  options,
  selected,
  onSelect,
}: {
  title: string;
  options: string[];
  selected: string | null;
  onSelect: (v: string | null) => void;
}) {
  if (options.length === 0) return null;
  return (
    <div>
      <h4 className="mb-2 text-xs font-medium uppercase tracking-wide text-neutral-500">{title}</h4>
      <ul className="space-y-1">
        {options.map((o) => (
          <li key={o}>
            <button
              onClick={() => onSelect(selected === o ? null : o)}
              className={cn(
                "w-full rounded px-2 py-1 text-left capitalize",
                selected === o ? "bg-neutral-900 text-white" : "hover:bg-neutral-100",
              )}
            >
              {o}
            </button>
          </li>
        ))}
      </ul>
    </div>
  );
}

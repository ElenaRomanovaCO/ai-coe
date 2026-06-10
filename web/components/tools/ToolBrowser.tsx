"use client";

import { useMemo, useState } from "react";
import Link from "next/link";

import { Input } from "@/components/ui/input";
import { costLabel, type ToolSummary } from "@/lib/tools";
import { cn } from "@/lib/utils";

// Client-side filtering over the full tool corpus (small N) for instant feedback —
// same pattern as AssetBrowser. Facets (category / cost / stage) are derived from the
// data; the text box covers name/stack/tag substring search.
export function ToolBrowser({ tools }: { tools: ToolSummary[] }) {
  const [category, setCategory] = useState<string | null>(null);
  const [cost, setCost] = useState<string | null>(null);
  const [stage, setStage] = useState<number | null>(null);
  const [text, setText] = useState("");

  const categories = useMemo(
    () => [...new Set(tools.map((t) => t.category))].filter(Boolean).sort(),
    [tools],
  );
  const costs = useMemo(
    () => [...new Set(tools.map((t) => t.cost_model))].filter(Boolean).sort(),
    [tools],
  );
  const stages = useMemo(
    () => [...new Set(tools.flatMap((t) => t.ai_stage_fit))].sort((a, b) => a - b),
    [tools],
  );

  const filtered = useMemo(() => {
    const q = text.trim().toLowerCase();
    return tools.filter((t) => {
      if (category && t.category !== category) return false;
      if (cost && t.cost_model !== cost) return false;
      if (stage !== null && !t.ai_stage_fit.includes(stage)) return false;
      if (q) {
        const hay = `${t.name} ${t.category} ${t.stack.join(" ")} ${t.tags.join(" ")}`.toLowerCase();
        if (!hay.includes(q)) return false;
      }
      return true;
    });
  }, [tools, category, cost, stage, text]);

  return (
    <div className="flex gap-6">
      <aside className="w-56 shrink-0 space-y-5 text-sm">
        <Input
          placeholder="Search tools, stack, tags…"
          value={text}
          onChange={(e) => setText(e.target.value)}
        />
        <FilterGroup
          title="Category"
          options={categories}
          selected={category}
          onSelect={setCategory}
          format={(s) => s.replace(/-/g, " ")}
        />
        <FilterGroup
          title="Cost model"
          options={costs}
          selected={cost}
          onSelect={setCost}
          format={costLabel}
        />
        <div>
          <h4 className="mb-2 text-xs font-medium uppercase tracking-wide text-neutral-500">
            AI Stage
          </h4>
          <div className="flex flex-wrap gap-1">
            {stages.map((s) => (
              <button
                key={s}
                onClick={() => setStage(stage === s ? null : s)}
                className={cn(
                  "h-7 w-7 rounded border text-xs",
                  stage === s
                    ? "border-neutral-900 bg-neutral-900 text-white"
                    : "border-neutral-300 hover:bg-neutral-100",
                )}
              >
                {s}
              </button>
            ))}
          </div>
        </div>
      </aside>

      <div className="flex-1">
        <p className="mb-3 text-sm text-neutral-500">
          {filtered.length} of {tools.length} tools
        </p>
        {filtered.length === 0 ? (
          <p className="mt-12 text-center text-neutral-400">No tools match those filters.</p>
        ) : (
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {filtered.map((t) => (
              <ToolCard key={t.id} tool={t} />
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

function ToolCard({ tool }: { tool: ToolSummary }) {
  return (
    <Link
      href={`/modules/tools-repo/${tool.id}`}
      className="flex flex-col rounded-lg border border-neutral-200 p-4 transition-colors hover:border-neutral-400 hover:bg-neutral-50"
    >
      <div className="mb-2 flex flex-wrap items-center gap-2">
        <span className="rounded bg-neutral-900 px-1.5 py-0.5 text-[11px] font-medium capitalize text-white">
          {tool.category.replace(/-/g, " ")}
        </span>
        <span className="text-xs text-neutral-500">{costLabel(tool.cost_model)}</span>
      </div>
      <h3 className="mb-1 font-semibold leading-snug text-neutral-900">{tool.name}</h3>
      {tool.ai_stage_fit.length > 0 && (
        <p className="mb-3 text-xs text-neutral-500">Stages {tool.ai_stage_fit.join(", ")}</p>
      )}
      {tool.tags.length > 0 && (
        <div className="mt-auto flex flex-wrap gap-1">
          {tool.tags.slice(0, 4).map((t) => (
            <span key={t} className="rounded bg-neutral-100 px-1.5 py-0.5 text-[11px] text-neutral-600">
              {t}
            </span>
          ))}
        </div>
      )}
    </Link>
  );
}

function FilterGroup({
  title,
  options,
  selected,
  onSelect,
  format = (s) => s,
}: {
  title: string;
  options: string[];
  selected: string | null;
  onSelect: (v: string | null) => void;
  format?: (s: string) => string;
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
              {format(o)}
            </button>
          </li>
        ))}
      </ul>
    </div>
  );
}

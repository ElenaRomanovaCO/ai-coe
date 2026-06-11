"use client";

import { useMemo, useState } from "react";
import Link from "next/link";
import { Puzzle } from "lucide-react";

import { Input } from "@/components/ui/input";
import {
  CATEGORY_STYLE,
  TOOL_STYLE,
  categoryLabel,
  toolLabel,
  type ExchangeEntry,
} from "@/lib/exchange";
import { cn } from "@/lib/utils";

// Client-side filtering over the catalog (small N) for instant feedback — same shape as
// AssetBrowser. Tool + category facets are derived from the data; text matches name,
// summary, and tags.
export function ExchangeBrowser({ entries }: { entries: ExchangeEntry[] }) {
  const [tool, setTool] = useState<string | null>(null);
  const [category, setCategory] = useState<string | null>(null);
  const [text, setText] = useState("");

  const tools = useMemo(
    () => [...new Set(entries.map((e) => e.tool))].filter(Boolean).sort(),
    [entries],
  );
  const categories = useMemo(
    () => [...new Set(entries.map((e) => e.category))].filter(Boolean).sort(),
    [entries],
  );

  const filtered = useMemo(() => {
    const q = text.trim().toLowerCase();
    return entries.filter((e) => {
      if (tool && e.tool !== tool) return false;
      if (category && e.category !== category) return false;
      if (q) {
        const hay = `${e.name} ${e.summary} ${e.tags.join(" ")}`.toLowerCase();
        if (!hay.includes(q)) return false;
      }
      return true;
    });
  }, [entries, tool, category, text]);

  return (
    <div className="flex gap-6">
      <aside className="w-56 shrink-0 space-y-5 text-sm">
        <Input
          placeholder="Search the exchange…"
          value={text}
          onChange={(e) => setText(e.target.value)}
        />
        <FilterGroup title="Tool" options={tools} selected={tool} onSelect={setTool} format={toolLabel} />
        <FilterGroup
          title="Category"
          options={categories}
          selected={category}
          onSelect={setCategory}
          format={categoryLabel}
        />
      </aside>

      <div className="flex-1">
        <p className="mb-3 text-sm text-neutral-500">
          {filtered.length} of {entries.length} entries
        </p>
        {filtered.length === 0 ? (
          <p className="mt-12 text-center text-neutral-400">No entries match those filters.</p>
        ) : (
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {filtered.map((e) => (
              <EntryCard key={e.id} entry={e} />
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

function EntryCard({ entry }: { entry: ExchangeEntry }) {
  return (
    <Link
      href={`/modules/exchange/${entry.id}`}
      className="flex flex-col rounded-lg border border-neutral-200 p-4 transition-colors hover:border-indigo-300 hover:bg-neutral-50"
    >
      <div className="mb-2 flex items-center gap-2">
        <Puzzle className="h-4 w-4 shrink-0 text-neutral-400" />
        <span
          className={cn(
            "rounded border px-1.5 py-0.5 text-[10px] font-medium",
            TOOL_STYLE[entry.tool] ?? "border-neutral-200 bg-neutral-100 text-neutral-600",
          )}
        >
          {toolLabel(entry.tool)}
        </span>
        <span
          className={cn(
            "rounded border px-1.5 py-0.5 text-[10px] font-medium",
            CATEGORY_STYLE[entry.category] ?? "border-neutral-200 bg-neutral-100 text-neutral-600",
          )}
        >
          {categoryLabel(entry.category)}
        </span>
      </div>
      <p className="text-sm font-medium text-neutral-900">{entry.name}</p>
      <p className="mt-1 line-clamp-2 text-xs text-neutral-500">{entry.summary}</p>
      {entry.tags.length > 0 && (
        <p className="mt-2 truncate text-[11px] text-neutral-400">{entry.tags.join(" · ")}</p>
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
                "w-full rounded px-2 py-1 text-left",
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

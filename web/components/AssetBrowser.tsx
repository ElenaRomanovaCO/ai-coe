"use client";

import { useMemo, useState } from "react";

import { AssetCard } from "@/components/AssetCard";
import { Input } from "@/components/ui/input";
import type { AssetSummary } from "@/lib/assets";
import { cn } from "@/lib/utils";

// Client-side filtering over the full seed list (small N) for instant feedback.
// Semantic search is available through Chat (search_knowledge_base); this box is a
// fast title/tag/type substring filter.
export function AssetBrowser({ assets }: { assets: AssetSummary[] }) {
  const [industry, setIndustry] = useState<string | null>(null);
  const [assetType, setAssetType] = useState<string | null>(null);
  const [stage, setStage] = useState<number | null>(null);
  const [text, setText] = useState("");

  const industries = useMemo(
    () => [...new Set(assets.map((a) => a.industry))].sort(),
    [assets],
  );
  const types = useMemo(() => [...new Set(assets.map((a) => a.type))].sort(), [assets]);
  const stages = useMemo(
    () => [...new Set(assets.map((a) => a.ai_stage))].sort((a, b) => a - b),
    [assets],
  );

  const filtered = useMemo(() => {
    const q = text.trim().toLowerCase();
    return assets.filter((a) => {
      if (industry && a.industry !== industry) return false;
      if (assetType && a.type !== assetType) return false;
      if (stage !== null && a.ai_stage !== stage) return false;
      if (q) {
        const hay = `${a.title} ${a.type} ${a.tags.join(" ")}`.toLowerCase();
        if (!hay.includes(q)) return false;
      }
      return true;
    });
  }, [assets, industry, assetType, stage, text]);

  return (
    <div className="flex gap-6">
      <aside className="w-56 shrink-0 space-y-5 text-sm">
        <Input
          placeholder="Search assets…"
          value={text}
          onChange={(e) => setText(e.target.value)}
        />
        <FilterGroup
          title="Industry"
          options={industries}
          selected={industry}
          onSelect={setIndustry}
          format={(s) => s.replace(/-/g, " ")}
        />
        <FilterGroup
          title="Type"
          options={types}
          selected={assetType}
          onSelect={setAssetType}
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
          {filtered.length} of {assets.length} assets
        </p>
        {filtered.length === 0 ? (
          <p className="mt-12 text-center text-neutral-400">No assets match those filters.</p>
        ) : (
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {filtered.map((a) => (
              <AssetCard key={a.id} asset={a} />
            ))}
          </div>
        )}
      </div>
    </div>
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

"use client";

import { useMemo, useState, useTransition } from "react";
import Link from "next/link";
import { Radar, Sparkles } from "lucide-react";

import { listFeed } from "@/app/(authenticated)/modules/intelligence-feed/actions";
import {
  AI_STAGES,
  CATEGORY_STYLE,
  FEED_INDUSTRIES,
  RADAR_STATUS_STYLE,
  categoryLabel,
  type FeedItemSummary,
} from "@/lib/feed";
import { cn } from "@/lib/utils";

// Browse the feed with a personalization profile (industry + stage focus) that re-ranks
// the list server-side via AGENT-23 → WORKER-10, plus client-side category / radar
// filters over the returned items (same instant-feedback pattern as RegulationBrowser).
export function FeedBrowser({ initialItems }: { initialItems: FeedItemSummary[] }) {
  const [items, setItems] = useState<FeedItemSummary[]>(initialItems);
  const [industry, setIndustry] = useState<string>("cross-industry");
  const [stage, setStage] = useState<number>(2);
  const [category, setCategory] = useState<string | null>(null);
  const [radar, setRadar] = useState<string | null>(null);
  const [pending, startTransition] = useTransition();

  // Re-rank the whole feed for the chosen profile (does not filter — cross-industry
  // items still surface, just lower). This is the FR-042 personalization signal.
  function repersonalize(nextIndustry: string, nextStage: number) {
    startTransition(async () => {
      const res = await listFeed({
        user_profile: { industries: [nextIndustry], ai_stage: nextStage },
      });
      if (res.status === "ok") setItems(res.items);
    });
  }

  const categories = useMemo(
    () => [...new Set(items.map((i) => i.category))].filter(Boolean).sort(),
    [items],
  );
  const radars = useMemo(
    () => [...new Set(items.map((i) => i.radar_status).filter((r): r is string => !!r))].sort(),
    [items],
  );

  const filtered = useMemo(
    () =>
      items.filter((i) => {
        if (category && i.category !== category) return false;
        if (radar && i.radar_status !== radar) return false;
        return true;
      }),
    [items, category, radar],
  );

  return (
    <div className="flex gap-6">
      <aside className="w-60 shrink-0 space-y-5 text-sm">
        <div className="rounded-lg border border-indigo-100 bg-indigo-50/60 p-3">
          <div className="mb-2 flex items-center gap-1.5 text-xs font-semibold uppercase tracking-wide text-indigo-700">
            <Sparkles className="h-3.5 w-3.5" />
            Personalize
          </div>
          <label className="mb-1 block text-xs font-medium text-neutral-600">Industry focus</label>
          <select
            value={industry}
            onChange={(e) => {
              setIndustry(e.target.value);
              repersonalize(e.target.value, stage);
            }}
            className="mb-3 w-full rounded border border-neutral-300 bg-white px-2 py-1 text-sm capitalize"
          >
            {FEED_INDUSTRIES.map((i) => (
              <option key={i} value={i}>
                {i.replace(/-/g, " ")}
              </option>
            ))}
          </select>
          <label className="mb-1 block text-xs font-medium text-neutral-600">AI stage focus</label>
          <select
            value={stage}
            onChange={(e) => {
              const s = Number(e.target.value);
              setStage(s);
              repersonalize(industry, s);
            }}
            className="w-full rounded border border-neutral-300 bg-white px-2 py-1 text-sm"
          >
            {AI_STAGES.map((s) => (
              <option key={s} value={s}>
                Stage {s}
              </option>
            ))}
          </select>
          <p className="mt-2 text-[11px] leading-snug text-indigo-700/80">
            Reorders the feed for your focus and tailors each item&apos;s note.
          </p>
        </div>

        <FilterGroup title="Category" options={categories} selected={category} onSelect={setCategory} format={categoryLabel} />
        <FilterGroup title="Radar status" options={radars} selected={radar} onSelect={setRadar} format={(s) => s} />

        <Link
          href="/modules/intelligence-feed/radar"
          className="flex items-center gap-2 rounded-lg border border-neutral-200 px-3 py-2 text-sm font-medium text-neutral-700 hover:border-indigo-300 hover:bg-neutral-50"
        >
          <Radar className="h-4 w-4 text-indigo-600" />
          View release radar
        </Link>
      </aside>

      <div className="flex-1">
        <p className="mb-3 text-sm text-neutral-500">
          {filtered.length} of {items.length} items
          {pending && <span className="ml-2 text-indigo-500">· re-ranking…</span>}
        </p>
        {filtered.length === 0 ? (
          <p className="mt-12 text-center text-neutral-400">No items match those filters.</p>
        ) : (
          <ul className={cn("space-y-3", pending && "opacity-60")}>
            {filtered.map((item) => (
              <FeedItemCard key={item.id} item={item} industry={industry} stage={stage} />
            ))}
          </ul>
        )}
      </div>
    </div>
  );
}

function FeedItemCard({
  item,
  industry,
  stage,
}: {
  item: FeedItemSummary;
  industry: string;
  stage: number;
}) {
  // Carry the active profile to the detail page so its commentary opens pre-tailored.
  const href = `/modules/intelligence-feed/${item.id}?industry=${encodeURIComponent(industry)}&stage=${stage}`;
  const matchedIndustry = item.matched?.industries?.length ? item.matched.industries[0] : null;
  return (
    <li>
      <Link
        href={href}
        className="block rounded-lg border border-neutral-200 p-4 transition-colors hover:border-indigo-300 hover:bg-neutral-50"
      >
        <div className="mb-1.5 flex flex-wrap items-center gap-2">
          <span
            className={cn(
              "rounded border px-1.5 py-0.5 text-[10px] font-medium uppercase",
              CATEGORY_STYLE[item.category] ?? "border-neutral-200 bg-neutral-100 text-neutral-600",
            )}
          >
            {categoryLabel(item.category)}
          </span>
          {item.radar_status && (
            <span
              className={cn(
                "rounded border px-1.5 py-0.5 text-[10px] font-medium uppercase",
                RADAR_STATUS_STYLE[item.radar_status] ?? "border-neutral-200 bg-neutral-100 text-neutral-600",
              )}
            >
              {item.radar_status}
            </span>
          )}
          {item.published_at && (
            <span className="text-xs text-neutral-400">{item.published_at.slice(0, 10)}</span>
          )}
          {matchedIndustry && (
            <span className="ml-auto rounded-full bg-indigo-50 px-2 py-0.5 text-[10px] font-medium capitalize text-indigo-600">
              relevant to {matchedIndustry.replace(/-/g, " ")}
            </span>
          )}
        </div>
        <p className="text-sm font-medium text-neutral-900">{item.title}</p>
        {item.tags.length > 0 && (
          <p className="mt-1 truncate text-xs text-neutral-500">{item.tags.join(" · ")}</p>
        )}
      </Link>
    </li>
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

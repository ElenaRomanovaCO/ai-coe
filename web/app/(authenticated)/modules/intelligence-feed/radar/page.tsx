import Link from "next/link";
import { Radar } from "lucide-react";

import {
  CATEGORY_STYLE,
  RADAR_QUADRANTS,
  categoryLabel,
  type FeedItemSummary,
} from "@/lib/feed";
import { cn } from "@/lib/utils";

import { getRadar } from "../actions";

export const dynamic = "force-dynamic";

export default async function ReleaseRadarPage() {
  const radar = await getRadar();
  const total = RADAR_QUADRANTS.reduce((n, q) => n + (radar[q.key]?.length ?? 0), 0);

  return (
    <div className="mx-auto max-w-6xl">
      <nav className="mb-4 text-sm text-neutral-500">
        <Link href="/modules/intelligence-feed" className="hover:text-neutral-900">
          AI Intelligence Feed
        </Link>
        <span className="mx-2">/</span>
        <span className="text-neutral-700">Release Radar</span>
      </nav>

      <div className="mb-6">
        <h1 className="flex items-center gap-2 text-2xl font-semibold">
          <Radar className="h-6 w-6 text-indigo-600" />
          Release Radar
        </h1>
        <p className="mt-1 text-sm text-neutral-500">
          {total} tracked technologies and developments, sorted into Adopt / Trial / Assess / Hold.
        </p>
      </div>

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {RADAR_QUADRANTS.map((q) => (
          <RadarColumn
            key={q.key}
            label={q.label}
            blurb={q.blurb}
            accent={q.accent}
            items={radar[q.key] ?? []}
          />
        ))}
      </div>
    </div>
  );
}

function RadarColumn({
  label,
  blurb,
  accent,
  items,
}: {
  label: string;
  blurb: string;
  accent: string;
  items: FeedItemSummary[];
}) {
  return (
    <section className={cn("flex flex-col rounded-lg border p-3", accent)}>
      <header className="mb-3">
        <h2 className="text-sm font-semibold text-neutral-900">
          {label}
          <span className="ml-1.5 text-xs font-normal text-neutral-500">({items.length})</span>
        </h2>
        <p className="text-[11px] text-neutral-500">{blurb}</p>
      </header>
      {items.length === 0 ? (
        <p className="py-6 text-center text-xs text-neutral-400">Nothing here yet.</p>
      ) : (
        <ul className="space-y-2">
          {items.map((item) => (
            <li key={item.id}>
              <Link
                href={`/modules/intelligence-feed/${item.id}`}
                className="block rounded-md border border-white/80 bg-white p-2.5 shadow-sm transition-colors hover:border-indigo-300"
              >
                <div className="mb-1 flex items-center justify-between gap-2">
                  <span
                    className={cn(
                      "rounded border px-1 py-0.5 text-[9px] font-medium uppercase",
                      CATEGORY_STYLE[item.category] ?? "border-neutral-200 bg-neutral-100 text-neutral-600",
                    )}
                  >
                    {categoryLabel(item.category)}
                  </span>
                  {item.published_at && (
                    <span className="text-[10px] text-neutral-400">
                      {item.published_at.slice(0, 7)}
                    </span>
                  )}
                </div>
                <p className="text-xs font-medium leading-snug text-neutral-900">{item.title}</p>
              </Link>
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}

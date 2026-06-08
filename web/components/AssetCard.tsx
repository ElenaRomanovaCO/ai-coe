import Link from "next/link";

import type { AssetSummary } from "@/lib/assets";

// Presentational card linking to the asset detail page. Save/Rate/Flag live on the
// detail page (they need the client-side display name); the grid stays a fast,
// server-renderable list of links.
export function AssetCard({ asset }: { asset: AssetSummary }) {
  return (
    <Link
      href={`/modules/asset-library/${asset.id}`}
      className="flex flex-col rounded-lg border border-neutral-200 p-4 transition-colors hover:border-neutral-400 hover:bg-neutral-50"
    >
      <div className="mb-2 flex items-center gap-2">
        <span className="rounded bg-neutral-900 px-1.5 py-0.5 text-[11px] font-medium text-white">
          {asset.type}
        </span>
        <span className="text-xs text-neutral-500">Stage {asset.ai_stage}</span>
      </div>
      <h3 className="mb-1 font-semibold leading-snug text-neutral-900">{asset.title}</h3>
      <p className="mb-3 text-sm capitalize text-neutral-500">{asset.industry.replace(/-/g, " ")}</p>
      {asset.tags.length > 0 && (
        <div className="mt-auto flex flex-wrap gap-1">
          {asset.tags.slice(0, 4).map((t) => (
            <span key={t} className="rounded bg-neutral-100 px-1.5 py-0.5 text-[11px] text-neutral-600">
              {t}
            </span>
          ))}
        </div>
      )}
    </Link>
  );
}

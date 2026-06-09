import Link from "next/link";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import type { AssetSummary } from "@/lib/assets";

export function SavedAssetsCard({ assets }: { assets: AssetSummary[] }) {
  return (
    <Card className="h-full">
      <CardHeader className="flex-row items-center justify-between">
        <CardTitle>Saved Assets</CardTitle>
        <Link href="/modules/asset-library" className="text-xs text-neutral-500 hover:text-neutral-900">
          See all
        </Link>
      </CardHeader>
      <CardContent>
        {assets.length === 0 ? (
          <p className="text-sm text-neutral-400">
            No saved assets yet. Save assets from the Asset Library.
          </p>
        ) : (
          <ul className="space-y-2">
            {assets.slice(0, 5).map((a) => (
              <li key={a.id}>
                <Link
                  href={`/modules/asset-library/${a.id}`}
                  className="flex items-center justify-between gap-2 text-sm hover:underline"
                >
                  <span className="truncate">{a.title}</span>
                  <span className="shrink-0 rounded bg-neutral-100 px-1.5 py-0.5 text-[11px] text-neutral-600">
                    {a.type}
                  </span>
                </Link>
              </li>
            ))}
          </ul>
        )}
      </CardContent>
    </Card>
  );
}

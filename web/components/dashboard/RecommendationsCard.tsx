import Link from "next/link";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import type { AssetSummary } from "@/lib/assets";

export function RecommendationsCard({ assets }: { assets: AssetSummary[] }) {
  return (
    <Card className="h-full">
      <CardHeader>
        <CardTitle>Recommended for You</CardTitle>
      </CardHeader>
      <CardContent>
        {assets.length === 0 ? (
          <p className="text-sm text-neutral-400">Recommendations appear as you save and explore assets.</p>
        ) : (
          <ul className="space-y-2">
            {assets.slice(0, 5).map((a) => (
              <li key={a.id}>
                <Link
                  href={`/modules/asset-library/${a.id}`}
                  className="flex items-center justify-between gap-2 text-sm hover:underline"
                >
                  <span className="truncate">{a.title}</span>
                  <span className="shrink-0 text-[11px] capitalize text-neutral-500">
                    {a.industry.replace(/-/g, " ")}
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

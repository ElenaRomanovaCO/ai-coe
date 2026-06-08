"use client";

import { useEffect, useState, useSyncExternalStore, useTransition } from "react";
import { Bookmark, Flag, Star } from "lucide-react";

import { getAsset, flagAsset, rateAsset, saveAsset } from "@/app/(authenticated)/modules/asset-library/actions";
import { Button } from "@/components/ui/button";
import type { AssetAggregates } from "@/lib/assets";
import { getDisplayName } from "@/lib/auth";
import { cn } from "@/lib/utils";

// Interactive Save / Rate / Flag for the detail page. Server-rendered aggregates
// are passed in; on mount we fetch this user's state (needs the client-side
// display name), then each action round-trips through AGENT-03 and updates both
// the aggregate counts and the user's own state.
export function AssetActions({
  assetId,
  initialAggregates,
}: {
  assetId: string;
  initialAggregates: AssetAggregates;
}) {
  const [aggregates, setAggregates] = useState(initialAggregates);
  const [saved, setSaved] = useState(false);
  const [rating, setRating] = useState<number | null>(null);
  const [flagged, setFlagged] = useState(false);
  const [pending, startTransition] = useTransition();

  // Read the client-only display name without a hydration mismatch (server -> null,
  // client -> localStorage), the same way the header does.
  const name = useSyncExternalStore(
    () => () => {},
    () => getDisplayName(),
    () => null,
  );

  // Load this user's saved/rating/flag state once the name is known. setState here
  // runs in the promise callback (not synchronously in the effect body).
  useEffect(() => {
    if (!name) return;
    getAsset(assetId, name)
      .then((res) => {
        if (res.aggregates) setAggregates(res.aggregates);
        if (res.user) {
          setSaved(res.user.saved);
          setRating(res.user.rating);
          setFlagged(res.user.flagged);
        }
      })
      .catch(() => {});
  }, [assetId, name]);

  function apply(result: AssetAggregates & Record<string, unknown>) {
    setAggregates({
      average_rating: result.average_rating,
      rating_count: result.rating_count,
      flag_count: result.flag_count,
      saved_count: result.saved_count,
    });
  }

  function onSave() {
    if (!name) return;
    const next = !saved;
    setSaved(next);
    startTransition(async () => apply(await saveAsset(assetId, name, next)));
  }

  function onRate(value: number) {
    if (!name) return;
    setRating(value);
    startTransition(async () => apply(await rateAsset(assetId, name, value)));
  }

  function onFlag() {
    if (!name || flagged) return;
    setFlagged(true);
    startTransition(async () => apply(await flagAsset(assetId, name)));
  }

  if (!name) {
    return (
      <p className="text-sm text-neutral-500">Set a display name to save, rate, or flag assets.</p>
    );
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center gap-2">
        <Button variant={saved ? "default" : "outline"} size="sm" onClick={onSave} disabled={pending}>
          <Bookmark className={cn("h-4 w-4", saved && "fill-current")} />
          {saved ? "Saved" : "Save"}
        </Button>
        <Button
          variant={flagged ? "default" : "outline"}
          size="sm"
          onClick={onFlag}
          disabled={pending || flagged}
        >
          <Flag className={cn("h-4 w-4", flagged && "fill-current")} />
          {flagged ? "Flagged" : "Flag"}
        </Button>
      </div>

      <div>
        <div className="mb-1 flex gap-1">
          {[1, 2, 3, 4, 5].map((n) => (
            <button key={n} onClick={() => onRate(n)} disabled={pending} aria-label={`Rate ${n}`}>
              <Star
                className={cn(
                  "h-5 w-5",
                  (rating ?? 0) >= n ? "fill-yellow-400 text-yellow-400" : "text-neutral-300",
                )}
              />
            </button>
          ))}
        </div>
        <p className="text-xs text-neutral-500">
          {aggregates.average_rating !== null
            ? `${aggregates.average_rating} avg · ${aggregates.rating_count} rating${aggregates.rating_count === 1 ? "" : "s"}`
            : "No ratings yet"}
        </p>
      </div>

      <dl className="space-y-1 border-t border-neutral-200 pt-3 text-xs text-neutral-500">
        <div className="flex justify-between">
          <dt>Saved by</dt>
          <dd>{aggregates.saved_count}</dd>
        </div>
        <div className="flex justify-between">
          <dt>Flags</dt>
          <dd>{aggregates.flag_count}</dd>
        </div>
      </dl>
    </div>
  );
}

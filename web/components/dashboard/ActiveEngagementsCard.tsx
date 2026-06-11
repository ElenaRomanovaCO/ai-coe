"use client";

import { useEffect, useState, useSyncExternalStore } from "react";
import Link from "next/link";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { getDisplayName } from "@/lib/auth";
import { listPortfolio } from "@/app/(authenticated)/modules/project-health/actions";
import { BAND_DOT, bandLabel, type EngagementSummary } from "@/lib/health";
import { cn } from "@/lib/utils";

// Live with Module 18: reads the caller's portfolio from AGENT-17 (list_portfolio) and
// shows the riskiest engagements, linking into the Project Health module.
export function ActiveEngagementsCard() {
  const name = useSyncExternalStore(
    () => () => {},
    () => getDisplayName(),
    () => null,
  );

  const [engagements, setEngagements] = useState<EngagementSummary[] | null>(null);

  useEffect(() => {
    let active = true;
    if (!name) return;
    listPortfolio(name).then((res) => {
      if (active) setEngagements(res.status === "ok" ? res.engagements : []);
    });
    return () => {
      active = false;
    };
  }, [name]);

  return (
    <Card className="h-full">
      <CardHeader>
        <CardTitle className="flex items-center justify-between">
          Active Engagements
          <Link
            href="/modules/project-health"
            className="text-xs font-normal text-indigo-600 hover:underline"
          >
            View all
          </Link>
        </CardTitle>
      </CardHeader>
      <CardContent>
        {engagements === null ? (
          <p className="text-sm text-neutral-400">Loading…</p>
        ) : engagements.length === 0 ? (
          <p className="text-sm text-neutral-400">
            No active engagements.{" "}
            <Link href="/modules/project-health/new" className="text-indigo-600 hover:underline">
              Register one
            </Link>
            .
          </p>
        ) : (
          <ul className="space-y-2">
            {engagements.slice(0, 5).map((e) => (
              <li key={e.engagement_id}>
                <Link
                  href={`/modules/project-health/${e.engagement_id}`}
                  className="flex items-center gap-2 rounded-md px-2 py-1.5 hover:bg-neutral-50"
                >
                  <span className={cn("h-2 w-2 shrink-0 rounded-full", BAND_DOT[e.band])} />
                  <span className="min-w-0 flex-1 truncate text-sm text-neutral-800">{e.name}</span>
                  <span className="shrink-0 text-xs text-neutral-500">
                    {bandLabel(e.band)} · {e.risk_score}
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

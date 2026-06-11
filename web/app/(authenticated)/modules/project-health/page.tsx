"use client";

import { useEffect, useState, useSyncExternalStore } from "react";
import Link from "next/link";
import { Activity, Plus } from "lucide-react";

import { getDisplayName } from "@/lib/auth";
import { BAND_DOT, BAND_STYLE, bandLabel, type EngagementSummary } from "@/lib/health";
import { cn } from "@/lib/utils";

import { listPortfolio } from "./actions";

export default function ProjectHealthPage() {
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
    <div className="mx-auto max-w-6xl">
      <div className="mb-6 flex items-start justify-between gap-4">
        <div>
          <h1 className="flex items-center gap-2 text-2xl font-semibold">
            <Activity className="h-6 w-6 text-indigo-600" />
            Project Health
          </h1>
          <p className="mt-1 text-sm text-neutral-500">
            Your active AI engagements, ranked by current risk. Post updates to track health over
            time.
          </p>
        </div>
        <Link
          href="/modules/project-health/new"
          className="flex shrink-0 items-center gap-1.5 rounded-md bg-indigo-600 px-3 py-2 text-sm font-medium text-white hover:bg-indigo-700"
        >
          <Plus className="h-4 w-4" />
          Register engagement
        </Link>
      </div>

      {engagements === null ? (
        <p className="mt-12 text-center text-sm text-neutral-400">Loading portfolio…</p>
      ) : engagements.length === 0 ? (
        <p className="mt-12 text-center text-neutral-400">
          No engagements yet. Register one to start tracking its health.
        </p>
      ) : (
        <div className="overflow-hidden rounded-lg border border-neutral-200">
          <table className="w-full text-sm">
            <thead className="bg-neutral-50 text-left text-xs uppercase tracking-wide text-neutral-500">
              <tr>
                <th className="px-4 py-2 font-medium">Engagement</th>
                <th className="px-4 py-2 font-medium">Industry · Stage</th>
                <th className="px-4 py-2 font-medium">Updates</th>
                <th className="px-4 py-2 font-medium">Flags</th>
                <th className="px-4 py-2 font-medium">Health</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-neutral-100">
              {engagements.map((e) => (
                <tr key={e.engagement_id} className="hover:bg-neutral-50">
                  <td className="px-4 py-2.5">
                    <Link
                      href={`/modules/project-health/${e.engagement_id}`}
                      className="flex items-center gap-2 font-medium text-neutral-900 hover:text-indigo-700"
                    >
                      <span className={cn("h-2 w-2 shrink-0 rounded-full", BAND_DOT[e.band])} />
                      {e.name}
                    </Link>
                  </td>
                  <td className="px-4 py-2.5 capitalize text-neutral-600">
                    {e.industry ? e.industry.replace(/-/g, " ") : "—"} · Stage {e.ai_stage}
                  </td>
                  <td className="px-4 py-2.5 text-neutral-600">{e.update_count}</td>
                  <td className="px-4 py-2.5 text-neutral-600">{e.open_flags}</td>
                  <td className="px-4 py-2.5">
                    <span
                      className={cn(
                        "inline-flex items-center gap-1.5 rounded border px-2 py-0.5 text-xs font-medium",
                        BAND_STYLE[e.band],
                      )}
                    >
                      {bandLabel(e.band)} · {e.risk_score}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}

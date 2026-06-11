"use client";

import { useEffect, useState, useSyncExternalStore } from "react";
import Link from "next/link";
import { History } from "lucide-react";

import { getDisplayName } from "@/lib/auth";
import { type RetroSummary } from "@/lib/retros";

import { listRetros } from "./actions";

export default function RetrosPage() {
  const name = useSyncExternalStore(
    () => () => {},
    () => getDisplayName(),
    () => null,
  );

  const [retros, setRetros] = useState<RetroSummary[] | null>(null);

  useEffect(() => {
    let active = true;
    if (!name) return;
    listRetros(name).then((res) => {
      if (active) setRetros(res.status === "ok" ? res.retros : []);
    });
    return () => {
      active = false;
    };
  }, [name]);

  return (
    <div className="mx-auto max-w-5xl">
      <div className="mb-6">
        <h1 className="flex items-center gap-2 text-2xl font-semibold">
          <History className="h-6 w-6 text-indigo-600" />
          Retrospectives
        </h1>
        <p className="mt-1 text-sm text-neutral-500">
          Capture engagement learnings at close. Each retro extracts reusable insights into the
          knowledge base. Start one from an engagement in{" "}
          <Link href="/modules/project-health" className="text-indigo-600 hover:underline">
            Project Health
          </Link>
          .
        </p>
      </div>

      {retros === null ? (
        <p className="mt-12 text-center text-sm text-neutral-400">Loading…</p>
      ) : retros.length === 0 ? (
        <p className="mt-12 text-center text-neutral-400">
          No retrospectives yet. Open an engagement in Project Health and file one at close.
        </p>
      ) : (
        <ul className="space-y-3">
          {retros.map((r) => (
            <li key={r.retro_id}>
              <Link
                href={`/modules/retros/${r.retro_id}`}
                className="block rounded-lg border border-neutral-200 p-4 transition-colors hover:border-indigo-300 hover:bg-neutral-50"
              >
                <div className="flex items-center justify-between gap-3">
                  <div className="min-w-0">
                    <p className="text-sm font-medium text-neutral-900">
                      Retro · engagement {r.engagement_id}
                    </p>
                    <p className="mt-0.5 text-xs text-neutral-500">
                      {r.created_at.slice(0, 10)} · stage reassessed to {r.stage_reassessment}
                    </p>
                  </div>
                  <span className="shrink-0 rounded-full bg-indigo-50 px-2.5 py-0.5 text-xs font-medium text-indigo-700">
                    {r.insight_count} insight{r.insight_count === 1 ? "" : "s"}
                  </span>
                </div>
              </Link>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}

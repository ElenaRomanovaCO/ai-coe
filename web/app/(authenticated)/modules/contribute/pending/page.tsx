"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { AlertTriangle, Inbox } from "lucide-react";

import { Card, CardContent } from "@/components/ui/card";
import type { PendingItem } from "@/lib/contribute";

import { listPending } from "../actions";

export default function PendingQueuePage() {
  const [items, setItems] = useState<PendingItem[]>([]);
  const [loaded, setLoaded] = useState(false);

  useEffect(() => {
    listPending("pending")
      .then((r) => setItems(r.pending ?? []))
      .finally(() => setLoaded(true));
  }, []);

  return (
    <div className="mx-auto max-w-4xl">
      <nav className="mb-4 text-sm text-slate-500">
        <Link href="/modules/contribute" className="hover:text-slate-900">
          Contribute
        </Link>
        <span className="mx-2">/</span>
        <span className="text-slate-700">Curator Queue</span>
      </nav>

      <h1 className="mb-1 flex items-center gap-2 text-2xl font-semibold">
        <Inbox className="h-6 w-6 text-indigo-600" />
        Curator Queue
      </h1>
      <p className="mb-5 text-sm text-slate-500">
        Pending submissions awaiting review. Open one to anonymize, tag, and approve into the
        Asset Library.
      </p>

      {!loaded ? (
        <div className="space-y-3">
          {[0, 1, 2].map((i) => (
            <div key={i} className="h-16 animate-pulse rounded-lg bg-slate-100" />
          ))}
        </div>
      ) : items.length === 0 ? (
        <p className="text-sm text-slate-400">The queue is empty.</p>
      ) : (
        <div className="space-y-3">
          {items.map((p) => (
            <Link key={p.pending_id} href={`/modules/contribute/${p.pending_id}`}>
              <Card className="transition hover:border-indigo-300">
                <CardContent className="flex items-center justify-between gap-4 pt-6">
                  <div className="min-w-0">
                    <h3 className="truncate text-sm font-semibold text-slate-900">{p.title}</h3>
                    <div className="mt-1 flex flex-wrap items-center gap-x-3 text-xs text-slate-500">
                      <span>{p.display_name}</span>
                      <span className="capitalize">{(p.type || "").replace(/-/g, " ")}</span>
                      <span className="capitalize">{(p.industry || "").replace(/-/g, " ")}</span>
                      <span>{(p.created_at || "").slice(0, 10)}</span>
                    </div>
                  </div>
                  {p.flag_count > 0 && (
                    <span className="flex shrink-0 items-center gap-1 rounded bg-amber-50 px-2 py-1 text-xs font-medium text-amber-700">
                      <AlertTriangle className="h-3 w-3" />
                      {p.flag_count}
                    </span>
                  )}
                </CardContent>
              </Card>
            </Link>
          ))}
        </div>
      )}
    </div>
  );
}

"use client";

import { useMemo, useState } from "react";
import Link from "next/link";
import { BookMarked } from "lucide-react";

import { Input } from "@/components/ui/input";
import { type DecisionSummary } from "@/lib/decisions";
import { cn } from "@/lib/utils";

// Client-side filtering over the logged-decision set (small N) for instant feedback —
// same pattern as RegulationBrowser/FeedBrowser. Text matches the decision + tags;
// tag facets are derived from the data.
export function DecisionBrowser({ decisions }: { decisions: DecisionSummary[] }) {
  const [text, setText] = useState("");
  const [tag, setTag] = useState<string | null>(null);

  const tags = useMemo(
    () => [...new Set(decisions.flatMap((d) => d.tags))].filter(Boolean).sort(),
    [decisions],
  );

  const filtered = useMemo(() => {
    const q = text.trim().toLowerCase();
    return decisions.filter((d) => {
      if (tag && !d.tags.includes(tag)) return false;
      if (q) {
        const hay = `${d.decision} ${d.tags.join(" ")}`.toLowerCase();
        if (!hay.includes(q)) return false;
      }
      return true;
    });
  }, [decisions, text, tag]);

  return (
    <div className="flex gap-6">
      <aside className="w-56 shrink-0 space-y-5 text-sm">
        <Input
          placeholder="Search decisions, tags…"
          value={text}
          onChange={(e) => setText(e.target.value)}
        />
        {tags.length > 0 && (
          <div>
            <h4 className="mb-2 text-xs font-medium uppercase tracking-wide text-neutral-500">
              Tags
            </h4>
            <ul className="flex flex-wrap gap-1.5">
              {tags.map((t) => (
                <li key={t}>
                  <button
                    onClick={() => setTag(tag === t ? null : t)}
                    className={cn(
                      "rounded-full border px-2 py-0.5 text-xs",
                      tag === t
                        ? "border-indigo-500 bg-indigo-600 text-white"
                        : "border-neutral-300 text-neutral-600 hover:border-indigo-400",
                    )}
                  >
                    {t}
                  </button>
                </li>
              ))}
            </ul>
          </div>
        )}
      </aside>

      <div className="flex-1">
        <p className="mb-3 text-sm text-neutral-500">
          {filtered.length} of {decisions.length} decisions
        </p>
        {filtered.length === 0 ? (
          <p className="mt-12 text-center text-neutral-400">
            No decisions match. Log one to get started.
          </p>
        ) : (
          <ul className="space-y-3">
            {filtered.map((d) => (
              <li key={d.decision_id}>
                <Link
                  href={`/modules/decisions/${d.decision_id}`}
                  className="block rounded-lg border border-neutral-200 p-4 transition-colors hover:border-indigo-300 hover:bg-neutral-50"
                >
                  <div className="flex items-start gap-3">
                    <BookMarked className="mt-0.5 h-5 w-5 shrink-0 text-neutral-400" />
                    <div className="min-w-0 flex-1">
                      <p className="text-sm font-medium text-neutral-900">{d.decision}</p>
                      <div className="mt-1 flex flex-wrap items-center gap-2">
                        {d.created_at && (
                          <span className="text-xs text-neutral-400">
                            {d.created_at.slice(0, 10)}
                          </span>
                        )}
                        {d.outcome && (
                          <span className="rounded bg-green-50 px-1.5 py-0.5 text-[10px] text-green-700">
                            outcome logged
                          </span>
                        )}
                        {d.tags.slice(0, 5).map((t) => (
                          <span
                            key={t}
                            className="rounded-full bg-neutral-100 px-2 py-0.5 text-[10px] text-neutral-600"
                          >
                            {t}
                          </span>
                        ))}
                      </div>
                    </div>
                  </div>
                </Link>
              </li>
            ))}
          </ul>
        )}
      </div>
    </div>
  );
}

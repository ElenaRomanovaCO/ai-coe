"use client";

import { useMemo, useState } from "react";
import Link from "next/link";
import { AlertTriangle, Boxes } from "lucide-react";

import { Input } from "@/components/ui/input";
import type { EvaluationSummary } from "@/lib/vendorEval";
import { cn } from "@/lib/utils";

// Client-side filtering over the evaluation corpus (small N) for instant feedback —
// same pattern as the other browse modules. Category facet is derived from the data;
// stale entries (past the re-verification window) carry a warning badge.
export function VendorEvalBrowser({ evaluations }: { evaluations: EvaluationSummary[] }) {
  const [category, setCategory] = useState<string | null>(null);
  const [text, setText] = useState("");

  const categories = useMemo(
    () => [...new Set(evaluations.map((e) => e.category))].filter(Boolean).sort(),
    [evaluations],
  );

  const filtered = useMemo(() => {
    const q = text.trim().toLowerCase();
    return evaluations.filter((e) => {
      if (category && e.category !== category) return false;
      if (q) {
        const hay = `${e.title} ${e.category} ${e.vendors_compared.join(" ")}`.toLowerCase();
        if (!hay.includes(q)) return false;
      }
      return true;
    });
  }, [evaluations, category, text]);

  return (
    <div className="flex gap-6">
      <aside className="w-56 shrink-0 space-y-5 text-sm">
        <Input
          placeholder="Search evaluations, vendors…"
          value={text}
          onChange={(e) => setText(e.target.value)}
        />
        {categories.length > 0 && (
          <div>
            <h4 className="mb-2 text-xs font-medium uppercase tracking-wide text-neutral-500">
              Category
            </h4>
            <ul className="space-y-1">
              {categories.map((c) => (
                <li key={c}>
                  <button
                    onClick={() => setCategory(category === c ? null : c)}
                    className={cn(
                      "w-full rounded px-2 py-1 text-left capitalize",
                      category === c ? "bg-neutral-900 text-white" : "hover:bg-neutral-100",
                    )}
                  >
                    {c.replace(/-/g, " ")}
                  </button>
                </li>
              ))}
            </ul>
          </div>
        )}
      </aside>

      <div className="flex-1">
        <p className="mb-3 text-sm text-neutral-500">
          {filtered.length} of {evaluations.length} evaluations
        </p>
        {filtered.length === 0 ? (
          <p className="mt-12 text-center text-neutral-400">No evaluations match those filters.</p>
        ) : (
          <ul className="space-y-3">
            {filtered.map((e) => (
              <EvaluationCard key={e.id} evaluation={e} />
            ))}
          </ul>
        )}
      </div>
    </div>
  );
}

function EvaluationCard({ evaluation: e }: { evaluation: EvaluationSummary }) {
  return (
    <li>
      <Link
        href={`/modules/vendor-eval/${e.id}`}
        className="block rounded-lg border border-neutral-200 p-4 transition-colors hover:border-indigo-300 hover:bg-neutral-50"
      >
        <div className="flex items-start gap-3">
          <Boxes className="mt-0.5 h-5 w-5 shrink-0 text-neutral-400" />
          <div className="min-w-0 flex-1">
            <div className="mb-1 flex flex-wrap items-center gap-2">
              <span className="rounded bg-neutral-100 px-2 py-0.5 text-xs capitalize text-neutral-700">
                {e.category.replace(/-/g, " ")}
              </span>
              {e.last_verified && (
                <span className="text-xs text-neutral-400">Verified {e.last_verified.slice(0, 10)}</span>
              )}
              {e.stale && (
                <span className="inline-flex items-center gap-1 rounded border border-amber-200 bg-amber-100 px-1.5 py-0.5 text-[10px] font-medium uppercase text-amber-700">
                  <AlertTriangle className="h-3 w-3" />
                  Stale
                </span>
              )}
            </div>
            <p className="text-sm font-medium text-neutral-900">{e.title}</p>
            {e.vendors_compared.length > 0 && (
              <p className="mt-1 truncate text-xs text-neutral-500">
                {e.vendors_compared.join(" · ")}
              </p>
            )}
          </div>
        </div>
      </Link>
    </li>
  );
}

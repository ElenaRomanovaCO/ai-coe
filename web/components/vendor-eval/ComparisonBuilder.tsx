"use client";

import { useState } from "react";
import { Download, GitCompare } from "lucide-react";

import { buildComparison } from "@/app/(authenticated)/modules/vendor-eval/actions";
import { MarkdownRenderer } from "@/components/MarkdownRenderer";
import { Button } from "@/components/ui/button";
import type { ComparisonResult, EvaluationSummary } from "@/lib/vendorEval";
import { cn } from "@/lib/utils";

const MAX_SELECT = 4;

// Pick 2-4 evaluations, build a side-by-side comparison (deterministic table +
// AGENT-13 insights), and download it as markdown. The agent is non-streaming, so a
// plain server action is the right fit (same transport as the other modules).
export function ComparisonBuilder({ evaluations }: { evaluations: EvaluationSummary[] }) {
  const [selected, setSelected] = useState<string[]>([]);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<ComparisonResult | null>(null);

  function toggle(id: string) {
    setSelected((prev) => {
      if (prev.includes(id)) return prev.filter((x) => x !== id);
      if (prev.length >= MAX_SELECT) return prev; // cap at 4
      return [...prev, id];
    });
  }

  async function onCompare() {
    if (selected.length < 2 || submitting) return;
    setSubmitting(true);
    setError(null);
    try {
      const res = await buildComparison(selected);
      if (res.status === "ok") {
        setResult(res);
      } else {
        setError(res.message || "Could not build the comparison.");
      }
    } catch {
      setError("Something went wrong building the comparison. Please try again.");
    } finally {
      setSubmitting(false);
    }
  }

  function onDownload() {
    if (!result) return;
    const blob = new Blob([result.comparison_markdown], { type: "text/markdown" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `${result.comparison_id}.md`;
    a.click();
    URL.revokeObjectURL(url);
  }

  return (
    <div className="space-y-6">
      <div className="rounded-lg border border-neutral-200 p-4">
        <div className="mb-3 flex items-center justify-between">
          <h2 className="text-sm font-semibold">
            Select evaluations{" "}
            <span className="font-normal text-neutral-400">({selected.length}/{MAX_SELECT})</span>
          </h2>
          <Button onClick={onCompare} disabled={selected.length < 2 || submitting} size="sm">
            <GitCompare className="h-4 w-4" />
            {submitting ? "Comparing…" : "Compare"}
          </Button>
        </div>
        <ul className="grid gap-2 sm:grid-cols-2">
          {evaluations.map((e) => {
            const checked = selected.includes(e.id);
            const atCap = !checked && selected.length >= MAX_SELECT;
            return (
              <li key={e.id}>
                <label
                  className={cn(
                    "flex cursor-pointer items-start gap-2 rounded-md border p-3 text-sm transition-colors",
                    checked
                      ? "border-indigo-400 bg-indigo-50"
                      : atCap
                        ? "cursor-not-allowed border-neutral-200 opacity-50"
                        : "border-neutral-200 hover:bg-neutral-50",
                  )}
                >
                  <input
                    type="checkbox"
                    className="mt-0.5"
                    checked={checked}
                    disabled={atCap}
                    onChange={() => toggle(e.id)}
                  />
                  <span className="min-w-0">
                    <span className="block font-medium text-neutral-900">{e.title}</span>
                    <span className="block truncate text-xs capitalize text-neutral-500">
                      {e.category.replace(/-/g, " ")}
                      {e.stale ? " · stale" : ""}
                    </span>
                  </span>
                </label>
              </li>
            );
          })}
        </ul>
        {error && <p className="mt-3 text-sm text-red-600">{error}</p>}
      </div>

      {result && (
        <div className="space-y-6">
          <div className="rounded-lg border border-neutral-200 p-4">
            <div className="mb-3 flex items-center justify-between">
              <h2 className="text-sm font-semibold">Key insights</h2>
              <Button onClick={onDownload} size="sm" variant="outline">
                <Download className="h-4 w-4" />
                Download .md
              </Button>
            </div>
            <ul className="list-disc space-y-1 pl-5 text-sm text-neutral-700">
              {result.insights.map((ins, i) => (
                <li key={i}>{ins}</li>
              ))}
            </ul>
          </div>
          <div className="overflow-x-auto rounded-lg border border-neutral-200 p-4">
            <MarkdownRenderer>{result.comparison_markdown}</MarkdownRenderer>
          </div>
        </div>
      )}
    </div>
  );
}

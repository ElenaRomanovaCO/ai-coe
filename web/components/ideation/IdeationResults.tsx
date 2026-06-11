"use client";

import { useState } from "react";
import Link from "next/link";
import { ChevronDown, Download, ExternalLink } from "lucide-react";

import {
  EFFORT_STYLE,
  IMPACT_STYLE,
  type Level,
  type UseCaseCandidate,
} from "@/lib/ideation";
import { cn } from "@/lib/utils";

const IMPACT_ROWS: Level[] = ["high", "medium", "low"];
const EFFORT_COLS: Level[] = ["low", "medium", "high"];

export function IdeationResults({
  candidates,
  markdown,
  ideationId,
}: {
  candidates: UseCaseCandidate[];
  markdown: string;
  ideationId: string;
}) {
  function onExport() {
    const blob = new Blob([markdown], { type: "text/markdown" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `${ideationId}.md`;
    a.click();
    URL.revokeObjectURL(url);
  }

  // Rank index by candidate id, for the matrix chips.
  const rankById = new Map(candidates.map((c, i) => [c.id, i + 1]));

  return (
    <div className="space-y-8">
      <section>
        <div className="mb-2 flex items-center justify-between">
          <h2 className="text-sm font-semibold uppercase tracking-wide text-neutral-500">
            Impact vs. effort
          </h2>
          {markdown && (
            <button
              onClick={onExport}
              className="flex items-center gap-1.5 rounded-md border border-neutral-300 px-2.5 py-1.5 text-xs font-medium text-neutral-700 hover:border-indigo-300 hover:bg-neutral-50"
            >
              <Download className="h-3.5 w-3.5" />
              Export markdown
            </button>
          )}
        </div>
        <Matrix candidates={candidates} rankById={rankById} />
      </section>

      <section>
        <h2 className="mb-3 text-sm font-semibold uppercase tracking-wide text-neutral-500">
          Ranked candidates
        </h2>
        <ul className="space-y-3">
          {candidates.map((c, i) => (
            <CandidateCard key={c.id} candidate={c} rank={i + 1} />
          ))}
        </ul>
      </section>
    </div>
  );
}

function Matrix({
  candidates,
  rankById,
}: {
  candidates: UseCaseCandidate[];
  rankById: Map<string, number>;
}) {
  const cell = (impact: Level, effort: Level) =>
    candidates.filter((c) => c.impact === impact && c.effort === effort);

  return (
    <div className="overflow-x-auto">
      <div className="inline-grid grid-cols-[auto_repeat(3,7rem)] gap-1 text-xs">
        <div />
        {EFFORT_COLS.map((e) => (
          <div key={e} className="pb-1 text-center font-medium capitalize text-neutral-500">
            {e} effort
          </div>
        ))}
        {IMPACT_ROWS.map((impact) => (
          <Row key={impact} impact={impact} cell={cell} rankById={rankById} />
        ))}
      </div>
      <p className="mt-2 text-xs text-neutral-400">
        Top-left (high impact · low effort) = quick wins. Numbers match the ranked list below.
      </p>
    </div>
  );
}

function Row({
  impact,
  cell,
  rankById,
}: {
  impact: Level;
  cell: (impact: Level, effort: Level) => UseCaseCandidate[];
  rankById: Map<string, number>;
}) {
  return (
    <>
      <div className="flex items-center pr-2 text-right font-medium capitalize text-neutral-500">
        {impact} impact
      </div>
      {EFFORT_COLS.map((effort) => {
        const items = cell(impact, effort);
        const isQuickWin = impact === "high" && effort === "low";
        return (
          <div
            key={effort}
            className={cn(
              "flex min-h-[3.5rem] flex-wrap content-start gap-1 rounded border p-1.5",
              isQuickWin ? "border-green-300 bg-green-50" : "border-neutral-200 bg-neutral-50/60",
            )}
          >
            {items.map((c) => (
              <span
                key={c.id}
                title={c.title}
                className="inline-flex h-5 w-5 items-center justify-center rounded-full bg-indigo-600 text-[10px] font-semibold text-white"
              >
                {rankById.get(c.id)}
              </span>
            ))}
          </div>
        );
      })}
    </>
  );
}

function CandidateCard({ candidate: c, rank }: { candidate: UseCaseCandidate; rank: number }) {
  const [open, setOpen] = useState(rank === 1); // top candidate expanded by default

  return (
    <li className="rounded-lg border border-neutral-200">
      <button
        onClick={() => setOpen((v) => !v)}
        className="flex w-full items-center gap-3 px-4 py-3 text-left"
      >
        <span className="inline-flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-indigo-600 text-xs font-semibold text-white">
          {rank}
        </span>
        <span className="min-w-0 flex-1">
          <span className="block truncate text-sm font-medium text-neutral-900">{c.title}</span>
        </span>
        <span className={cn("rounded border px-1.5 py-0.5 text-[10px] font-medium uppercase", IMPACT_STYLE[c.impact])}>
          {c.impact} impact
        </span>
        <span className={cn("rounded border px-1.5 py-0.5 text-[10px] font-medium uppercase", EFFORT_STYLE[c.effort])}>
          {c.effort} effort
        </span>
        <ChevronDown
          className={cn("h-4 w-4 shrink-0 text-neutral-400 transition-transform", open && "rotate-180")}
        />
      </button>
      {open && (
        <div className="space-y-3 border-t border-neutral-100 px-4 py-3 text-sm">
          {c.description && <p className="text-neutral-700">{c.description}</p>}
          {c.prerequisites.length > 0 && (
            <div>
              <p className="mb-1 text-xs font-semibold uppercase tracking-wide text-neutral-500">
                Prerequisites
              </p>
              <ul className="list-disc space-y-0.5 pl-5 text-neutral-700">
                {c.prerequisites.map((p, i) => (
                  <li key={i}>{p}</li>
                ))}
              </ul>
            </div>
          )}
          {c.rationale && (
            <p className="text-neutral-600">
              <span className="font-medium text-neutral-700">Why this fits: </span>
              {c.rationale}
            </p>
          )}
          {c.reference_example_asset_id && c.reference_example_url && (
            <Link
              href={c.reference_example_url}
              className="inline-flex items-center gap-1.5 text-xs font-medium text-indigo-600 hover:text-indigo-800"
            >
              <ExternalLink className="h-3.5 w-3.5" />
              Reference: {c.reference_example_title ?? c.reference_example_asset_id}
            </Link>
          )}
        </div>
      )}
    </li>
  );
}

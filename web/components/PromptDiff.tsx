"use client";

import { useSyncExternalStore } from "react";

import { lastRunKey, lineDiff, type DiffRow } from "@/lib/prompts";
import { cn } from "@/lib/utils";

// Read a prompt's last-run output from sessionStorage in a React-19-safe way
// (client-only value; null on the server snapshot).
function useLastOutput(promptId: string): string | null {
  return useSyncExternalStore(
    () => () => {},
    () => {
      try {
        const raw = sessionStorage.getItem(lastRunKey(promptId));
        return raw ? (JSON.parse(raw).output as string) : null;
      } catch {
        return null;
      }
    },
    () => null,
  );
}

interface Side {
  id: string;
  title: string;
  version: number;
  prompt_text: string;
}

// Side-by-side diff of two prompt versions (left = base, right = other), plus the
// last-known run outputs if both have been run this session (stashed by PromptRunner).
export function PromptDiff({ left, right }: { left: Side; right: Side }) {
  const rows = lineDiff(left.prompt_text, right.prompt_text);
  const leftOut = useLastOutput(left.id);
  const rightOut = useLastOutput(right.id);

  return (
    <div className="space-y-8">
      <section>
        <div className="mb-2 grid grid-cols-2 gap-4 text-sm font-medium text-neutral-700">
          <div>
            v{left.version} · {left.title}
          </div>
          <div>
            v{right.version} · {right.title}
          </div>
        </div>
        <div className="overflow-hidden rounded-lg border border-neutral-200 font-mono text-[12px]">
          {rows.map((row, i) => (
            <DiffLine key={i} row={row} />
          ))}
        </div>
      </section>

      {(leftOut || rightOut) && (
        <section>
          <h2 className="mb-2 text-sm font-semibold">Last run outputs (this session)</h2>
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
            <OutputBox label={`v${left.version}`} text={leftOut} />
            <OutputBox label={`v${right.version}`} text={rightOut} />
          </div>
        </section>
      )}
    </div>
  );
}

function DiffLine({ row }: { row: DiffRow }) {
  return (
    <div className="grid grid-cols-2">
      <pre
        className={cn(
          "overflow-x-auto whitespace-pre-wrap border-b border-r border-neutral-100 px-3 py-1",
          row.op === "remove" && "bg-red-50 text-red-800",
        )}
      >
        {row.left ?? ""}
      </pre>
      <pre
        className={cn(
          "overflow-x-auto whitespace-pre-wrap border-b border-neutral-100 px-3 py-1",
          row.op === "add" && "bg-green-50 text-green-800",
        )}
      >
        {row.right ?? ""}
      </pre>
    </div>
  );
}

function OutputBox({ label, text }: { label: string; text: string | null }) {
  return (
    <div className="rounded-lg border border-neutral-200 p-3">
      <p className="mb-2 text-xs font-medium uppercase tracking-wide text-neutral-500">{label}</p>
      {text ? (
        <pre className="whitespace-pre-wrap text-[13px] text-neutral-700">{text}</pre>
      ) : (
        <p className="text-sm text-neutral-400">Not run yet this session.</p>
      )}
    </div>
  );
}

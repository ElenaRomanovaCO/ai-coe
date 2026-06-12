import { RESULT_STYLE, type Control } from "@/lib/vendorVetting";
import { cn } from "@/lib/utils";

// Presentational: renders the per-control pass/gap/unknown breakdown from WORKER-20.
export function VettingChecklist({ controls }: { controls: Control[] }) {
  if (controls.length === 0) {
    return <p className="text-sm text-neutral-400">Run an assessment to see the control checklist.</p>;
  }
  return (
    <ul className="divide-y divide-neutral-100">
      {controls.map((c, i) => (
        <li key={i} className="flex items-center justify-between gap-3 py-2">
          <div className="min-w-0">
            <p className="text-sm text-neutral-800">{c.control}</p>
            <p className="truncate text-xs text-neutral-400">{c.detail}</p>
          </div>
          <span
            className={cn(
              "shrink-0 rounded border px-1.5 py-0.5 text-[10px] font-medium uppercase",
              RESULT_STYLE[c.result],
            )}
          >
            {c.result}
          </span>
        </li>
      ))}
    </ul>
  );
}

"use client";

import { useMemo, useState } from "react";
import Link from "next/link";
import { FileText } from "lucide-react";

import { Input } from "@/components/ui/input";
import {
  STATUS_STYLE,
  geoLabel,
  type RegulationSummary,
} from "@/lib/compliance";
import { cn } from "@/lib/utils";

// Client-side filtering over the full reg corpus (small N) for instant feedback —
// same pattern as AssetBrowser. The text box covers the "use case type" axis by
// matching the name and tags. Geography / industry / status are faceted from the data.
export function RegulationBrowser({ regulations }: { regulations: RegulationSummary[] }) {
  const [geo, setGeo] = useState<string | null>(null);
  const [industry, setIndustry] = useState<string | null>(null);
  const [status, setStatus] = useState<string | null>(null);
  const [text, setText] = useState("");

  const geos = useMemo(
    () => [...new Set(regulations.map((r) => r.geo))].filter(Boolean).sort(),
    [regulations],
  );
  const industries = useMemo(
    () => [...new Set(regulations.flatMap((r) => r.industry_scope))].filter(Boolean).sort(),
    [regulations],
  );
  const statuses = useMemo(
    () => [...new Set(regulations.map((r) => r.status))].filter(Boolean).sort(),
    [regulations],
  );

  const filtered = useMemo(() => {
    const q = text.trim().toLowerCase();
    return regulations.filter((r) => {
      if (geo && r.geo !== geo) return false;
      if (industry && !r.industry_scope.includes(industry)) return false;
      if (status && r.status !== status) return false;
      if (q) {
        const hay = `${r.name} ${r.tags.join(" ")}`.toLowerCase();
        if (!hay.includes(q)) return false;
      }
      return true;
    });
  }, [regulations, geo, industry, status, text]);

  return (
    <div className="flex gap-6">
      <aside className="w-56 shrink-0 space-y-5 text-sm">
        <Input
          placeholder="Search use cases, tags…"
          value={text}
          onChange={(e) => setText(e.target.value)}
        />
        <FilterGroup title="Geography" options={geos} selected={geo} onSelect={setGeo} format={geoLabel} />
        <FilterGroup
          title="Industry"
          options={industries}
          selected={industry}
          onSelect={setIndustry}
          format={(s) => s.replace(/-/g, " ")}
        />
        <FilterGroup
          title="Status"
          options={statuses}
          selected={status}
          onSelect={setStatus}
          format={(s) => s.replace(/-/g, " ")}
        />
      </aside>

      <div className="flex-1">
        <p className="mb-3 text-sm text-neutral-500">
          {filtered.length} of {regulations.length} regulations
        </p>
        {filtered.length === 0 ? (
          <p className="mt-12 text-center text-neutral-400">No regulations match those filters.</p>
        ) : (
          <ul className="space-y-3">
            {filtered.map((r) => (
              <RegulationCard key={r.id} reg={r} />
            ))}
          </ul>
        )}
      </div>
    </div>
  );
}

function RegulationCard({ reg }: { reg: RegulationSummary }) {
  return (
    <li>
      <Link
        href={`/modules/compliance-tracker/${reg.id}`}
        className="block rounded-lg border border-neutral-200 p-4 transition-colors hover:border-indigo-300 hover:bg-neutral-50"
      >
        <div className="flex items-start gap-3">
          <FileText className="mt-0.5 h-5 w-5 shrink-0 text-neutral-400" />
          <div className="min-w-0 flex-1">
            <div className="mb-1 flex flex-wrap items-center gap-2">
              <span className="rounded bg-neutral-100 px-2 py-0.5 text-xs text-neutral-700">
                {geoLabel(reg.geo)}
              </span>
              {reg.status && (
                <span
                  className={cn(
                    "rounded border px-1.5 py-0.5 text-[10px] font-medium uppercase",
                    STATUS_STYLE[reg.status] ?? "border-neutral-200 bg-neutral-100 text-neutral-600",
                  )}
                >
                  {reg.status.replace(/-/g, " ")}
                </span>
              )}
              {reg.effective_date && (
                <span className="text-xs text-neutral-400">Effective {reg.effective_date.slice(0, 10)}</span>
              )}
            </div>
            <p className="text-sm font-medium text-neutral-900">{reg.name}</p>
            {reg.industry_scope.length > 0 && (
              <p className="mt-1 truncate text-xs capitalize text-neutral-500">
                {reg.industry_scope.map((s) => s.replace(/-/g, " ")).join(" · ")}
              </p>
            )}
          </div>
        </div>
      </Link>
    </li>
  );
}

function FilterGroup({
  title,
  options,
  selected,
  onSelect,
  format = (s) => s,
}: {
  title: string;
  options: string[];
  selected: string | null;
  onSelect: (v: string | null) => void;
  format?: (s: string) => string;
}) {
  if (options.length === 0) return null;
  return (
    <div>
      <h4 className="mb-2 text-xs font-medium uppercase tracking-wide text-neutral-500">{title}</h4>
      <ul className="space-y-1">
        {options.map((o) => (
          <li key={o}>
            <button
              onClick={() => onSelect(selected === o ? null : o)}
              className={cn(
                "w-full rounded px-2 py-1 text-left capitalize",
                selected === o ? "bg-neutral-900 text-white" : "hover:bg-neutral-100",
              )}
            >
              {format(o)}
            </button>
          </li>
        ))}
      </ul>
    </div>
  );
}

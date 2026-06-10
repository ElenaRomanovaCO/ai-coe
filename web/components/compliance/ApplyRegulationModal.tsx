"use client";

import { useEffect, useState } from "react";
import { Check, ClipboardCheck, Minus, X } from "lucide-react";

import { applyRegulation } from "@/app/(authenticated)/modules/compliance-tracker/actions";
import { Button } from "@/components/ui/button";
import {
  GEOGRAPHIES,
  INDUSTRIES,
  type ApplyResult,
} from "@/lib/compliance";
import { cn } from "@/lib/utils";

const SELECT_CLASS =
  "w-full rounded-md border border-neutral-300 bg-white px-3 py-2 text-sm text-neutral-900 focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500";

export interface ApplyRegulationModalProps {
  regId: string;
  regName: string;
  defaultIndustry: string;
  defaultGeography: string;
}

// Opens from the regulation detail page: describe a use case, get a per-clause
// applicability checklist (WORKER-13) plus a plain-language note (AGENT-24's one
// Sonnet call). Non-streaming server action — same transport as the other modules.
export function ApplyRegulationModal({
  regId,
  regName,
  defaultIndustry,
  defaultGeography,
}: ApplyRegulationModalProps) {
  const [open, setOpen] = useState(false);
  const [useCase, setUseCase] = useState("");
  const [industry, setIndustry] = useState(defaultIndustry);
  const [geography, setGeography] = useState(defaultGeography);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<ApplyResult | null>(null);

  useEffect(() => {
    if (!open) return;
    function onKey(e: KeyboardEvent) {
      if (e.key === "Escape") setOpen(false);
    }
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [open]);

  async function onRun() {
    if (!useCase.trim() || submitting) return;
    setSubmitting(true);
    setError(null);
    try {
      const res = await applyRegulation({
        reg_id: regId,
        use_case_description: useCase.trim(),
        industry,
        geography,
      });
      if (res.status === "ok") {
        setResult(res);
      } else {
        setError(res.message || "Could not assess applicability.");
      }
    } catch {
      setError("Something went wrong. Please try again.");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <>
      <Button size="sm" className="w-full" onClick={() => setOpen(true)}>
        <ClipboardCheck className="h-4 w-4" />
        Apply to a use case
      </Button>

      {open && (
        <div
          className="fixed inset-0 z-50 flex items-start justify-center overflow-y-auto bg-black/40 p-4 sm:items-center"
          onClick={() => setOpen(false)}
        >
          <div
            className="my-8 w-full max-w-2xl rounded-lg border border-neutral-200 bg-white shadow-xl"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="flex items-center justify-between border-b border-neutral-200 px-5 py-3">
              <div className="min-w-0">
                <h2 className="text-sm font-semibold text-neutral-900">Apply to a use case</h2>
                <p className="truncate text-xs text-neutral-500">{regName}</p>
              </div>
              <button
                onClick={() => setOpen(false)}
                className="rounded p-1 text-neutral-400 hover:bg-neutral-100 hover:text-neutral-700"
                aria-label="Close"
              >
                <X className="h-4 w-4" />
              </button>
            </div>

            <div className="space-y-4 px-5 py-4">
              <div>
                <label className="mb-1 block text-sm font-medium text-neutral-700">
                  Describe the AI use case
                </label>
                <textarea
                  className={cn(SELECT_CLASS, "min-h-24 resize-y")}
                  value={useCase}
                  onChange={(e) => setUseCase(e.target.value)}
                  placeholder="e.g. a clinical imaging classifier that flags suspected fractures"
                />
              </div>
              <div className="grid gap-4 sm:grid-cols-2">
                <div>
                  <label className="mb-1 block text-sm font-medium text-neutral-700">Industry</label>
                  <select
                    className={SELECT_CLASS}
                    value={industry}
                    onChange={(e) => setIndustry(e.target.value)}
                  >
                    {INDUSTRIES.map((i) => (
                      <option key={i} value={i}>
                        {i.replace(/-/g, " ")}
                      </option>
                    ))}
                  </select>
                </div>
                <div>
                  <label className="mb-1 block text-sm font-medium text-neutral-700">Geography</label>
                  <select
                    className={SELECT_CLASS}
                    value={geography}
                    onChange={(e) => setGeography(e.target.value)}
                  >
                    {GEOGRAPHIES.map((g) => (
                      <option key={g} value={g}>
                        {g}
                      </option>
                    ))}
                  </select>
                </div>
              </div>

              {error && <p className="text-sm text-red-600">{error}</p>}

              <Button onClick={onRun} disabled={submitting || !useCase.trim()}>
                {submitting ? "Assessing…" : "Check applicability"}
              </Button>

              {result && <ApplyResultView result={result} />}
            </div>
          </div>
        </div>
      )}
    </>
  );
}

function ApplyResultView({ result }: { result: ApplyResult }) {
  return (
    <div className="space-y-4 border-t border-neutral-200 pt-4">
      <div>
        <h3 className="mb-1 text-xs font-semibold uppercase tracking-wide text-neutral-500">
          Assessment
        </h3>
        <p className="whitespace-pre-wrap text-sm leading-relaxed text-neutral-700">
          {result.narrative}
        </p>
      </div>
      <div>
        <h3 className="mb-2 text-xs font-semibold uppercase tracking-wide text-neutral-500">
          Applicability by clause
        </h3>
        <ul className="space-y-2">
          {result.applicability.map((item, i) => (
            <li
              key={i}
              className="flex items-start gap-2 rounded-lg border border-neutral-200 p-3"
            >
              <span
                className={cn(
                  "mt-0.5 flex h-5 w-5 shrink-0 items-center justify-center rounded-full",
                  item.applies ? "bg-green-100 text-green-700" : "bg-neutral-100 text-neutral-400",
                )}
              >
                {item.applies ? <Check className="h-3.5 w-3.5" /> : <Minus className="h-3.5 w-3.5" />}
              </span>
              <div className="min-w-0">
                <p className="text-sm font-medium text-neutral-900">{item.clause}</p>
                <p className="text-xs text-neutral-500">{item.reason}</p>
              </div>
            </li>
          ))}
        </ul>
      </div>
    </div>
  );
}

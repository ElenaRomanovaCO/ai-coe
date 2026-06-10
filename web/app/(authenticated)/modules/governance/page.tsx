"use client";

import { useEffect, useState, useSyncExternalStore } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { ShieldCheck } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { getDisplayName } from "@/lib/auth";
import {
  DATA_TYPES,
  GEOGRAPHIES,
  INDUSTRIES,
  type ReviewSummary,
} from "@/lib/governance";
import { cn } from "@/lib/utils";

import { listReviews, runGovernanceCheck } from "./actions";

const SELECT_CLASS =
  "w-full rounded-md border border-neutral-300 bg-white px-3 py-2 text-sm text-neutral-900 focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500";

export default function GovernancePage() {
  const router = useRouter();
  const name = useSyncExternalStore(
    () => () => {},
    () => getDisplayName(),
    () => null,
  );

  const [industry, setIndustry] = useState("healthcare");
  const [geography, setGeography] = useState("EU");
  const [dataTypes, setDataTypes] = useState<string[]>(["phi"]);
  const [useCase, setUseCase] = useState("");
  const [extra, setExtra] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const [past, setPast] = useState<ReviewSummary[]>([]);
  const [loaded, setLoaded] = useState(false);

  useEffect(() => {
    if (!name) return;
    listReviews(name)
      .then((r) => {
        setPast(r.reviews ?? []);
        setLoaded(true);
      })
      .catch(() => setLoaded(true));
  }, [name]);

  function toggleDataType(dt: string) {
    setDataTypes((prev) => (prev.includes(dt) ? prev.filter((d) => d !== dt) : [...prev, dt]));
  }

  async function onSubmit() {
    if (!name || !useCase.trim() || submitting) return;
    setSubmitting(true);
    setError(null);
    try {
      const res = await runGovernanceCheck({
        display_name: name,
        industry,
        geography,
        data_types: dataTypes,
        ai_use_case_type: useCase.trim(),
        engagement_context: extra.trim() || undefined,
      });
      if (res.status === "ok" && res.review_id) {
        router.push(`/modules/governance/${res.review_id}`);
      } else {
        setError(res.message || "The governance check could not be completed.");
        setSubmitting(false);
      }
    } catch {
      setError("Something went wrong running the check. Please try again.");
      setSubmitting(false);
    }
  }

  if (!name) {
    return (
      <div className="mx-auto max-w-3xl">
        <h1 className="text-2xl font-semibold">Governance &amp; Risk Checker</h1>
        <p className="mt-2 text-sm text-neutral-500">
          Set a display name (log out and back in) to run a governance check.
        </p>
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-5xl">
      <div className="mb-6">
        <h1 className="flex items-center gap-2 text-2xl font-semibold">
          <ShieldCheck className="h-6 w-6 text-indigo-600" />
          Governance &amp; Risk Checker
        </h1>
        <p className="mt-1 text-sm text-neutral-500">
          Describe the engagement and get a pre-delivery risk checklist with the regulations it
          triggers and remediation guidance.
        </p>
      </div>

      <div className="grid gap-6 lg:grid-cols-3">
        <Card className="lg:col-span-2">
          <CardHeader>
            <CardTitle>Engagement context</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
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

            <div>
              <label className="mb-1 block text-sm font-medium text-neutral-700">Data types</label>
              <div className="flex flex-wrap gap-2">
                {DATA_TYPES.map((dt) => (
                  <button
                    key={dt}
                    type="button"
                    onClick={() => toggleDataType(dt)}
                    className={cn(
                      "rounded-full border px-3 py-1 text-xs uppercase tracking-wide transition-colors",
                      dataTypes.includes(dt)
                        ? "border-indigo-600 bg-indigo-600 text-white"
                        : "border-neutral-300 bg-white text-neutral-600 hover:border-indigo-400",
                    )}
                  >
                    {dt}
                  </button>
                ))}
              </div>
            </div>

            <div>
              <label className="mb-1 block text-sm font-medium text-neutral-700">
                AI use case type
              </label>
              <Input
                value={useCase}
                onChange={(e) => setUseCase(e.target.value)}
                placeholder="e.g. clinical decision support"
              />
            </div>

            <div>
              <label className="mb-1 block text-sm font-medium text-neutral-700">
                Additional context <span className="font-normal text-neutral-400">(optional)</span>
              </label>
              <textarea
                className={cn(SELECT_CLASS, "min-h-20 resize-y")}
                value={extra}
                onChange={(e) => setExtra(e.target.value)}
                placeholder="Anything else about the engagement, data flows, or constraints."
              />
            </div>

            {error && <p className="text-sm text-red-600">{error}</p>}

            <Button onClick={onSubmit} disabled={submitting || !useCase.trim()}>
              {submitting ? "Running check…" : "Run governance check"}
            </Button>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Past reviews</CardTitle>
          </CardHeader>
          <CardContent>
            {!loaded ? (
              <div className="space-y-2">
                {[0, 1, 2].map((i) => (
                  <div key={i} className="h-12 animate-pulse rounded bg-neutral-100" />
                ))}
              </div>
            ) : past.length === 0 ? (
              <p className="text-sm text-neutral-400">No reviews yet.</p>
            ) : (
              <ul className="space-y-3">
                {past.map((r) => (
                  <li key={r.review_id}>
                    <Link
                      href={`/modules/governance/${r.review_id}`}
                      className="block rounded-md border border-neutral-200 p-3 hover:bg-neutral-50"
                    >
                      <div className="mb-1 flex items-center justify-between text-xs text-neutral-500">
                        <span>{(r.created_at || "").slice(0, 10)}</span>
                        <span>{r.item_count ?? 0} items</span>
                      </div>
                      <p className="truncate text-sm font-medium text-neutral-800">
                        {r.ai_use_case_type || "Governance review"}
                      </p>
                      <p className="truncate text-xs capitalize text-neutral-500">
                        {(r.industry || "").replace(/-/g, " ")} · {r.geography}
                      </p>
                    </Link>
                  </li>
                ))}
              </ul>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}

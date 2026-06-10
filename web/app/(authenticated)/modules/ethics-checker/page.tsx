"use client";

import { useEffect, useState, useSyncExternalStore } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { Scale } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { getDisplayName } from "@/lib/auth";
import {
  DATA_TYPES,
  DECISION_TYPES,
  GEOGRAPHIES,
  INDUSTRIES,
  type EthicsReviewSummary,
} from "@/lib/ethics";
import { cn } from "@/lib/utils";

import { listReviews, runEthicsReview } from "./actions";

const SELECT_CLASS =
  "w-full rounded-md border border-neutral-300 bg-white px-3 py-2 text-sm text-neutral-900 focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500";

export default function EthicsCheckerPage() {
  const router = useRouter();
  const name = useSyncExternalStore(
    () => () => {},
    () => getDisplayName(),
    () => null,
  );

  const [useCase, setUseCase] = useState("");
  const [decisionType, setDecisionType] = useState("automated");
  const [industry, setIndustry] = useState("financial-services");
  const [geography, setGeography] = useState("US");
  const [dataTypes, setDataTypes] = useState<string[]>(["financial"]);
  const [populations, setPopulations] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const [past, setPast] = useState<EthicsReviewSummary[]>([]);
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
      const res = await runEthicsReview({
        display_name: name,
        use_case: useCase.trim(),
        data_types: dataTypes,
        affected_populations: populations
          .split(",")
          .map((p) => p.trim())
          .filter(Boolean),
        decision_type: decisionType,
        geography,
        industry,
      });
      if (res.status === "ok" && res.review_id) {
        router.push(`/modules/ethics-checker/${res.review_id}`);
      } else {
        setError(res.message || "The ethics review could not be completed.");
        setSubmitting(false);
      }
    } catch {
      setError("Something went wrong running the review. Please try again.");
      setSubmitting(false);
    }
  }

  if (!name) {
    return (
      <div className="mx-auto max-w-3xl">
        <h1 className="text-2xl font-semibold">AI Ethics &amp; Bias Checker</h1>
        <p className="mt-2 text-sm text-neutral-500">
          Set a display name (log out and back in) to run an ethics review.
        </p>
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-5xl">
      <div className="mb-6">
        <h1 className="flex items-center gap-2 text-2xl font-semibold">
          <Scale className="h-6 w-6 text-indigo-600" />
          AI Ethics &amp; Bias Checker
        </h1>
        <p className="mt-1 text-sm text-neutral-500">
          Describe an AI use case and get a structured ethics review — bias risks, fairness,
          explainability, human oversight, and EU AI Act risk tier.
        </p>
      </div>

      <div className="grid gap-6 lg:grid-cols-3">
        <Card className="lg:col-span-2">
          <CardHeader>
            <CardTitle>Use case</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div>
              <label className="mb-1 block text-sm font-medium text-neutral-700">
                What does the system do?
              </label>
              <textarea
                className={cn(SELECT_CLASS, "min-h-20 resize-y")}
                value={useCase}
                onChange={(e) => setUseCase(e.target.value)}
                placeholder="e.g. an automated model that approves or denies consumer loan applications"
              />
            </div>

            <div className="grid gap-4 sm:grid-cols-2">
              <div>
                <label className="mb-1 block text-sm font-medium text-neutral-700">
                  Decision type
                </label>
                <select
                  className={SELECT_CLASS}
                  value={decisionType}
                  onChange={(e) => setDecisionType(e.target.value)}
                >
                  {DECISION_TYPES.map((d) => (
                    <option key={d} value={d}>
                      {d.replace(/-/g, " ")}
                    </option>
                  ))}
                </select>
              </div>
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
              <div>
                <label className="mb-1 block text-sm font-medium text-neutral-700">
                  Affected populations
                </label>
                <Input
                  value={populations}
                  onChange={(e) => setPopulations(e.target.value)}
                  placeholder="comma-separated, e.g. low-income, minorities"
                />
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

            {error && <p className="text-sm text-red-600">{error}</p>}

            <Button onClick={onSubmit} disabled={submitting || !useCase.trim()}>
              {submitting ? "Running review…" : "Run ethics review"}
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
                      href={`/modules/ethics-checker/${r.review_id}`}
                      className="block rounded-md border border-neutral-200 p-3 hover:bg-neutral-50"
                    >
                      <div className="mb-1 flex items-center justify-between text-xs text-neutral-500">
                        <span>{(r.created_at || "").slice(0, 10)}</span>
                        <span>{r.risk_count ?? 0} risks</span>
                      </div>
                      <p className="truncate text-sm font-medium text-neutral-800">
                        {r.use_case || "Ethics review"}
                      </p>
                      <p className="truncate text-xs capitalize text-neutral-500">
                        {(r.decision_type || "").replace(/-/g, " ")}
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

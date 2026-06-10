import Link from "next/link";
import { notFound } from "next/navigation";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import {
  SEVERITY_ORDER,
  SEVERITY_STYLE,
  TIER_STYLE,
  type BiasRisk,
  type FrameworkMapping,
} from "@/lib/ethics";
import { cn } from "@/lib/utils";

import { getReview } from "../actions";

export const dynamic = "force-dynamic";

export default async function EthicsReviewPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = await params;
  const res = await getReview(id);
  if (res.status !== "ok" || !res.review_id) {
    notFound();
  }

  const {
    context,
    bias_risks,
    fairness_considerations,
    explainability_requirements,
    human_oversight_recommendations,
    frameworks,
    summary,
    created_at,
  } = res;

  return (
    <div className="mx-auto max-w-5xl">
      <nav className="mb-4 text-sm text-neutral-500">
        <Link href="/modules/ethics-checker" className="hover:text-neutral-900">
          AI Ethics &amp; Bias Checker
        </Link>
        <span className="mx-2">/</span>
        <span className="text-neutral-700">Review</span>
      </nav>

      <header className="mb-6">
        <div className="mb-2 flex flex-wrap items-center gap-2 text-xs">
          <span className="rounded bg-neutral-900 px-2 py-0.5 font-medium capitalize text-white">
            {(context.decision_type || "").replace(/-/g, " ")}
          </span>
          <span className="rounded bg-neutral-100 px-2 py-0.5 capitalize text-neutral-700">
            {(context.industry || "").replace(/-/g, " ")}
          </span>
          <span className="rounded bg-neutral-100 px-2 py-0.5 text-neutral-700">
            {context.geography}
          </span>
        </div>
        <h1 className="text-2xl font-semibold">{context.use_case || "Ethics Review"}</h1>
        {created_at && <p className="mt-1 text-xs text-neutral-400">{created_at.slice(0, 10)}</p>}
      </header>

      <div className="flex flex-col gap-6 lg:flex-row">
        <div className="min-w-0 flex-1 space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>Executive summary</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="whitespace-pre-wrap text-sm leading-relaxed text-neutral-700">
                {summary}
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Bias risks ({bias_risks.length})</CardTitle>
            </CardHeader>
            <CardContent className="space-y-6">
              {SEVERITY_ORDER.map((sev) => {
                const items = bias_risks.filter((r) => r.severity === sev);
                if (!items.length) return null;
                return (
                  <section key={sev}>
                    <h3 className="mb-2 text-xs font-semibold uppercase tracking-wide text-neutral-500">
                      {sev}
                    </h3>
                    <ul className="space-y-3">
                      {items.map((risk) => (
                        <RiskRow key={risk.id} risk={risk} />
                      ))}
                    </ul>
                  </section>
                );
              })}
            </CardContent>
          </Card>

          <ListCard title="Fairness considerations" items={fairness_considerations} />
          <ListCard title="Explainability requirements" items={explainability_requirements} />
          <ListCard title="Human-oversight recommendations" items={human_oversight_recommendations} />
        </div>

        <aside className="w-full shrink-0 space-y-4 lg:w-72">
          <Card>
            <CardHeader>
              <CardTitle>Regulatory mapping</CardTitle>
            </CardHeader>
            <CardContent>
              {frameworks.length === 0 ? (
                <p className="text-sm text-neutral-400">No frameworks mapped.</p>
              ) : (
                <ul className="space-y-3">
                  {frameworks.map((f) => (
                    <FrameworkRow key={f.framework} framework={f} />
                  ))}
                </ul>
              )}
            </CardContent>
          </Card>
        </aside>
      </div>
    </div>
  );
}

function RiskRow({ risk }: { risk: BiasRisk }) {
  return (
    <li className="rounded-lg border border-neutral-200 p-3">
      <div className="flex items-start gap-2">
        <span
          className={cn(
            "mt-0.5 shrink-0 rounded border px-1.5 py-0.5 text-[10px] font-medium uppercase",
            SEVERITY_STYLE[risk.severity],
          )}
        >
          {risk.severity}
        </span>
        <div className="min-w-0">
          <p className="text-[11px] uppercase tracking-wide text-neutral-400">
            {risk.category.replace(/_/g, " ")}
          </p>
          <p className="text-sm font-medium text-neutral-900">{risk.description}</p>
          {risk.mitigation && (
            <p className="mt-1 text-xs text-neutral-500">
              <span className="font-medium text-neutral-600">Mitigation:</span> {risk.mitigation}
            </p>
          )}
        </div>
      </div>
    </li>
  );
}

// Frameworks render as non-clickable badges; deep-links to regulation detail pages
// arrive with Module 25 (Compliance Tracker). reg_id is present only for regs that
// exist in the vault, so no dangling references either way.
function FrameworkRow({ framework }: { framework: FrameworkMapping }) {
  return (
    <li>
      <div className="mb-1 flex items-center gap-2">
        <span className="text-sm font-medium text-neutral-800">{framework.framework}</span>
        <span
          className={cn(
            "rounded border px-1.5 py-0.5 text-[10px] font-medium uppercase",
            TIER_STYLE[framework.tier] ?? "border-neutral-200 bg-neutral-100 text-neutral-600",
          )}
        >
          {framework.tier}
        </span>
      </div>
      <p className="text-xs text-neutral-500">{framework.note}</p>
    </li>
  );
}

function ListCard({ title, items }: { title: string; items: string[] }) {
  return (
    <Card>
      <CardHeader>
        <CardTitle>{title}</CardTitle>
      </CardHeader>
      <CardContent>
        {items.length === 0 ? (
          <p className="text-sm text-neutral-400">None.</p>
        ) : (
          <ul className="list-disc space-y-2 pl-5 text-sm text-neutral-700">
            {items.map((it, i) => (
              <li key={i}>{it}</li>
            ))}
          </ul>
        )}
      </CardContent>
    </Card>
  );
}

import Link from "next/link";
import { notFound } from "next/navigation";
import { Lightbulb } from "lucide-react";

import { INSIGHT_TYPE_STYLE, type Insight } from "@/lib/retros";
import { cn } from "@/lib/utils";

import { getRetro } from "../actions";

export const dynamic = "force-dynamic";

export default async function RetroDetailPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = await params;
  const res = await getRetro(id);
  if (res.status !== "ok" || !res.retro) {
    notFound();
  }

  const r = res.retro;
  const insights = res.insights ?? [];

  return (
    <div className="mx-auto max-w-5xl">
      <nav className="mb-4 text-sm text-neutral-500">
        <Link href="/modules/retros" className="hover:text-neutral-900">
          Retrospectives
        </Link>
        <span className="mx-2">/</span>
        <span className="text-neutral-700">Retro</span>
      </nav>

      <header className="mb-6">
        <h1 className="text-2xl font-semibold">Retrospective</h1>
        <p className="mt-1 text-sm text-neutral-500">
          Engagement{" "}
          <Link
            href={`/modules/project-health/${r.engagement_id}`}
            className="text-indigo-600 hover:underline"
          >
            {r.engagement_id}
          </Link>{" "}
          · {r.created_at.slice(0, 10)} · stage reassessed to {r.stage_reassessment}
        </p>
      </header>

      {/* Extracted insights — the reusable KB output, leads the page */}
      <section className="mb-8">
        <h2 className="mb-3 flex items-center gap-2 text-sm font-semibold uppercase tracking-wide text-neutral-500">
          <Lightbulb className="h-4 w-4 text-amber-500" />
          Extracted insights ({insights.length})
        </h2>
        {insights.length === 0 ? (
          <p className="text-sm text-neutral-400">No insights were extracted.</p>
        ) : (
          <ul className="space-y-3">
            {insights.map((i) => (
              <InsightCard key={i.insight_id} insight={i} />
            ))}
          </ul>
        )}
      </section>

      <section className="grid grid-cols-1 gap-6 md:grid-cols-2">
        <Block title="Use cases attempted" items={r.use_cases_attempted} />
        <Block title="Patterns used" items={r.patterns_used} mono />
        <Prose title="What worked" text={r.what_worked} />
        <Prose title="What failed" text={r.what_failed} />
        <Block title="Tools recommended" items={r.tools_recommended} />
        <Block title="Tools not recommended" items={r.tools_not_recommended} />
      </section>
    </div>
  );
}

function InsightCard({ insight: i }: { insight: Insight }) {
  return (
    <li className="rounded-lg border border-neutral-200 p-4">
      <div className="mb-1.5 flex items-center gap-2">
        <span
          className={cn(
            "rounded border px-1.5 py-0.5 text-[10px] font-medium uppercase",
            INSIGHT_TYPE_STYLE[i.type] ?? INSIGHT_TYPE_STYLE.general,
          )}
        >
          {i.type}
        </span>
        <span className="rounded bg-green-50 px-1.5 py-0.5 text-[10px] text-green-700">
          saved to knowledge base
        </span>
      </div>
      <p className="text-sm font-medium text-neutral-900">{i.statement}</p>
      {i.evidence && <p className="mt-1 text-xs text-neutral-500">{i.evidence}</p>}
      {i.asset_link && (
        <Link
          href={`/modules/asset-library/${i.asset_link}`}
          className="mt-1.5 inline-block text-xs font-medium text-indigo-600 hover:underline"
        >
          Related asset: {i.asset_link}
        </Link>
      )}
    </li>
  );
}

function Block({ title, items, mono }: { title: string; items: string[]; mono?: boolean }) {
  return (
    <div>
      <h3 className="mb-1 text-xs font-semibold uppercase tracking-wide text-neutral-500">{title}</h3>
      {items.length === 0 ? (
        <p className="text-sm text-neutral-400">—</p>
      ) : (
        <ul className="list-disc space-y-0.5 pl-5 text-sm text-neutral-700">
          {items.map((it, idx) => (
            <li key={idx} className={mono ? "font-mono text-xs" : undefined}>
              {it}
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}

function Prose({ title, text }: { title: string; text: string }) {
  return (
    <div>
      <h3 className="mb-1 text-xs font-semibold uppercase tracking-wide text-neutral-500">{title}</h3>
      <p className="whitespace-pre-wrap text-sm text-neutral-700">
        {text || <span className="text-neutral-400">—</span>}
      </p>
    </div>
  );
}

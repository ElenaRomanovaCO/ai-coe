import Link from "next/link";
import { notFound } from "next/navigation";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

import { getDecision, getSimilar } from "../actions";

export const dynamic = "force-dynamic";

export default async function DecisionDetailPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = await params;
  const [res, sim] = await Promise.all([getDecision(id), getSimilar(id)]);
  if (res.status !== "ok" || !res.decision) {
    notFound();
  }

  const d = res.decision;
  const similar = sim.status === "ok" ? sim.similar : [];

  return (
    <div className="mx-auto max-w-6xl">
      <nav className="mb-4 text-sm text-neutral-500">
        <Link href="/modules/decisions" className="hover:text-neutral-900">
          Decision Log
        </Link>
        <span className="mx-2">/</span>
        <span className="text-neutral-700">{d.decision}</span>
      </nav>

      <header className="mb-6">
        <h1 className="text-2xl font-semibold">{d.decision}</h1>
        <div className="mt-2 flex flex-wrap items-center gap-2 text-xs">
          {d.created_at && <span className="text-neutral-400">{d.created_at.slice(0, 10)}</span>}
          {d.engagement_id && (
            <span className="rounded bg-neutral-100 px-2 py-0.5 text-neutral-600">
              {d.engagement_id}
            </span>
          )}
          {d.tags.map((t) => (
            <span key={t} className="rounded-full bg-neutral-100 px-2 py-0.5 text-neutral-600">
              {t}
            </span>
          ))}
        </div>
      </header>

      <div className="flex flex-col gap-8 lg:flex-row">
        <article className="min-w-0 flex-1 space-y-5">
          <Section title="Context" body={d.context} />
          <div>
            <h2 className="mb-1 text-xs font-semibold uppercase tracking-wide text-neutral-500">
              Alternatives considered
            </h2>
            {d.alternatives.length > 0 ? (
              <ul className="list-disc space-y-1 pl-5 text-sm text-neutral-700">
                {d.alternatives.map((a, i) => (
                  <li key={i}>{a}</li>
                ))}
              </ul>
            ) : (
              <p className="text-sm text-neutral-400">(none recorded)</p>
            )}
          </div>
          <Section title="Rationale" body={d.rationale} />
          <Section title="Outcome" body={d.outcome || ""} placeholder="(pending)" />
        </article>

        <aside className="w-full shrink-0 lg:w-80">
          <Card>
            <CardHeader>
              <CardTitle className="text-base">Similar decisions</CardTitle>
            </CardHeader>
            <CardContent>
              {similar.length === 0 ? (
                <p className="text-sm text-neutral-400">No similar decisions yet.</p>
              ) : (
                <ul className="space-y-2">
                  {similar.map((s) => (
                    <li key={s.decision_id}>
                      <Link
                        href={`/modules/decisions/${s.decision_id}`}
                        className="block rounded-md border border-neutral-200 p-2.5 transition-colors hover:border-indigo-300 hover:bg-neutral-50"
                      >
                        <p className="text-sm font-medium text-neutral-900">{s.decision}</p>
                        {s.tags.length > 0 && (
                          <p className="mt-0.5 truncate text-[11px] text-neutral-500">
                            {s.tags.join(" · ")}
                          </p>
                        )}
                      </Link>
                    </li>
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

function Section({ title, body, placeholder }: { title: string; body: string; placeholder?: string }) {
  return (
    <div>
      <h2 className="mb-1 text-xs font-semibold uppercase tracking-wide text-neutral-500">
        {title}
      </h2>
      <p className="whitespace-pre-wrap text-sm leading-relaxed text-neutral-700">
        {body || <span className="text-neutral-400">{placeholder ?? "(none)"}</span>}
      </p>
    </div>
  );
}

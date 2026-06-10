import Link from "next/link";
import { notFound } from "next/navigation";
import { FileText } from "lucide-react";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import {
  PRIORITY_ORDER,
  type ChecklistItem,
  type Priority,
  type RegulationMatch,
} from "@/lib/governance";
import { cn } from "@/lib/utils";

import { getReview } from "../actions";

export const dynamic = "force-dynamic";

const PRIORITY_STYLE: Record<Priority, string> = {
  critical: "bg-red-100 text-red-700 border-red-200",
  high: "bg-orange-100 text-orange-700 border-orange-200",
  medium: "bg-amber-100 text-amber-700 border-amber-200",
  low: "bg-neutral-100 text-neutral-600 border-neutral-200",
};

export default async function GovernanceReviewPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = await params;
  const res = await getReview(id);
  if (res.status !== "ok" || !res.review_id) {
    notFound();
  }

  const { context, regulations, checklist, summary, created_at } = res;
  const regName = new Map(regulations.map((r) => [r.id, r.name]));

  return (
    <div className="mx-auto max-w-5xl">
      <nav className="mb-4 text-sm text-neutral-500">
        <Link href="/modules/governance" className="hover:text-neutral-900">
          Governance &amp; Risk Checker
        </Link>
        <span className="mx-2">/</span>
        <span className="text-neutral-700">Review</span>
      </nav>

      <header className="mb-6">
        <div className="mb-2 flex flex-wrap items-center gap-2 text-xs">
          <span className="rounded bg-neutral-900 px-2 py-0.5 font-medium capitalize text-white">
            {(context.industry || "").replace(/-/g, " ")}
          </span>
          <span className="rounded bg-neutral-100 px-2 py-0.5 text-neutral-700">
            {context.geography}
          </span>
          {context.data_types?.map((d) => (
            <span key={d} className="rounded bg-neutral-100 px-2 py-0.5 uppercase text-neutral-600">
              {d}
            </span>
          ))}
        </div>
        <h1 className="text-2xl font-semibold">{context.ai_use_case_type || "Governance Review"}</h1>
        {created_at && (
          <p className="mt-1 text-xs text-neutral-400">{created_at.slice(0, 10)}</p>
        )}
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
              <CardTitle>Risk checklist ({checklist.length})</CardTitle>
            </CardHeader>
            <CardContent className="space-y-6">
              {PRIORITY_ORDER.map((p) => {
                const items = checklist.filter((c) => c.priority === p);
                if (!items.length) return null;
                return (
                  <section key={p}>
                    <h3 className="mb-2 text-xs font-semibold uppercase tracking-wide text-neutral-500">
                      {p}
                    </h3>
                    <ul className="space-y-3">
                      {items.map((item) => (
                        <ChecklistRow key={item.id} item={item} regName={regName} />
                      ))}
                    </ul>
                  </section>
                );
              })}
            </CardContent>
          </Card>
        </div>

        <aside className="w-full shrink-0 space-y-4 lg:w-72">
          <Card>
            <CardHeader>
              <CardTitle>Regulations considered</CardTitle>
            </CardHeader>
            <CardContent>
              {regulations.length === 0 ? (
                <p className="text-sm text-neutral-400">None matched.</p>
              ) : (
                <ul className="space-y-3">
                  {regulations.map((r) => (
                    <RegulationRow key={r.id} reg={r} />
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

function ChecklistRow({
  item,
  regName,
}: {
  item: ChecklistItem;
  regName: Map<string, string>;
}) {
  return (
    <li className="rounded-lg border border-neutral-200 p-3">
      <div className="flex items-start gap-2">
        <span
          className={cn(
            "mt-0.5 shrink-0 rounded border px-1.5 py-0.5 text-[10px] font-medium uppercase",
            PRIORITY_STYLE[item.priority],
          )}
        >
          {item.priority}
        </span>
        <div className="min-w-0">
          <p className="text-sm font-medium text-neutral-900">{item.statement}</p>
          {item.rationale && (
            <p className="mt-1 text-xs text-neutral-500">{item.rationale}</p>
          )}
          {item.regulation_links?.length > 0 && (
            <div className="mt-2 flex flex-wrap gap-1">
              {item.regulation_links.map((rid) => (
                <span
                  key={rid}
                  title={rid}
                  className="rounded border border-neutral-300 bg-white px-1.5 py-0.5 text-[11px] text-neutral-600"
                >
                  {regName.get(rid) || rid}
                </span>
              ))}
            </div>
          )}
        </div>
      </div>
    </li>
  );
}

function RegulationRow({ reg }: { reg: RegulationMatch }) {
  return (
    <li>
      <div className="flex items-start gap-2">
        <FileText className="mt-0.5 h-4 w-4 shrink-0 text-neutral-400" />
        <div className="min-w-0">
          <p className="text-sm font-medium text-neutral-800">{reg.name}</p>
          <p className="truncate text-xs text-neutral-400">{reg.id}</p>
          {reg.applicable_clauses && reg.applicable_clauses.length > 0 && (
            <p className="mt-1 text-xs text-neutral-500">
              {reg.applicable_clauses.slice(0, 3).join(" · ")}
            </p>
          )}
        </div>
      </div>
    </li>
  );
}

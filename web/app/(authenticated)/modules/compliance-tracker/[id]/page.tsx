import Link from "next/link";
import { notFound } from "next/navigation";

import { AssetChatPanelHook } from "@/components/AssetChatPanelHook";
import { ApplyRegulationModal } from "@/components/compliance/ApplyRegulationModal";
import { FrontmatterPanel } from "@/components/FrontmatterPanel";
import { MarkdownRenderer } from "@/components/MarkdownRenderer";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { STATUS_STYLE, geoLabel } from "@/lib/compliance";
import { cn } from "@/lib/utils";

import { getRegulation } from "../actions";

export const dynamic = "force-dynamic";

export default async function RegulationDetailPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = await params;
  const res = await getRegulation(id);
  if (res.status !== "ok" || !res.regulation) {
    notFound();
  }

  const { regulation, summary } = res;
  const fm = regulation.frontmatter ?? {};
  const geo = String(fm.geo ?? "");
  const status = String(fm.status ?? "");
  const scope = Array.isArray(fm.industry_scope) ? (fm.industry_scope as string[]) : [];
  // Sensible Apply-modal defaults from the regulation's own scope.
  const defaultIndustry = scope.find((s) => s !== "cross-industry") ?? scope[0] ?? "healthcare";
  const defaultGeography =
    geo === "eu" ? "EU" : geo === "us-state-ca" ? "California" : geo ? "US" : "EU";

  return (
    <div className="mx-auto max-w-6xl">
      <nav className="mb-4 text-sm text-neutral-500">
        <Link href="/modules/compliance-tracker" className="hover:text-neutral-900">
          Compliance Tracker
        </Link>
        <span className="mx-2">/</span>
        <span className="text-neutral-700">{regulation.name}</span>
      </nav>

      <header className="mb-6">
        <div className="mb-2 flex flex-wrap items-center gap-2 text-xs">
          {geo && (
            <span className="rounded bg-neutral-100 px-2 py-0.5 text-neutral-700">
              {geoLabel(geo)}
            </span>
          )}
          {status && (
            <span
              className={cn(
                "rounded border px-1.5 py-0.5 font-medium uppercase",
                STATUS_STYLE[status] ?? "border-neutral-200 bg-neutral-100 text-neutral-600",
              )}
            >
              {status.replace(/-/g, " ")}
            </span>
          )}
          {fm.effective_date ? (
            <span className="text-neutral-400">Effective {String(fm.effective_date).slice(0, 10)}</span>
          ) : null}
        </div>
        <h1 className="text-2xl font-semibold">{regulation.name}</h1>
      </header>

      <div className="flex flex-col gap-8 lg:flex-row">
        <article className="min-w-0 flex-1">
          {summary.summary && (
            <Card className="mb-6">
              <CardHeader>
                <CardTitle>Plain-language summary</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <p className="text-sm leading-relaxed text-neutral-700">{summary.summary}</p>
                {summary.key_requirements.length > 0 && (
                  <div>
                    <h3 className="mb-1 text-xs font-semibold uppercase tracking-wide text-neutral-500">
                      Key requirements
                    </h3>
                    <ul className="list-disc space-y-1 pl-5 text-sm text-neutral-700">
                      {summary.key_requirements.map((k, i) => (
                        <li key={i}>{k}</li>
                      ))}
                    </ul>
                  </div>
                )}
                {summary.sector_implications.length > 0 && (
                  <div>
                    <h3 className="mb-1 text-xs font-semibold uppercase tracking-wide text-neutral-500">
                      What this means for engagements
                    </h3>
                    <ul className="list-disc space-y-1 pl-5 text-sm text-neutral-700">
                      {summary.sector_implications.map((s, i) => (
                        <li key={i}>{s}</li>
                      ))}
                    </ul>
                  </div>
                )}
              </CardContent>
            </Card>
          )}
          <MarkdownRenderer>{regulation.body_markdown}</MarkdownRenderer>
        </article>

        <aside className="w-full shrink-0 space-y-6 lg:w-72">
          <ApplyRegulationModal
            regId={regulation.id}
            regName={regulation.name}
            defaultIndustry={defaultIndustry}
            defaultGeography={defaultGeography}
          />
          <AssetChatPanelHook
            assetId={regulation.id}
            assetTitle={regulation.name}
            assetContent={regulation.body_markdown}
            assetFrontmatter={fm}
          />
          <section className="rounded-lg border border-neutral-200 p-4">
            <h2 className="mb-3 text-sm font-semibold">Details</h2>
            <FrontmatterPanel frontmatter={fm} />
          </section>
        </aside>
      </div>
    </div>
  );
}

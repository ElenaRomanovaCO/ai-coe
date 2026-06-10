import Link from "next/link";
import { notFound } from "next/navigation";
import { AlertTriangle } from "lucide-react";

import { AssetChatPanelHook } from "@/components/AssetChatPanelHook";
import { FrontmatterPanel } from "@/components/FrontmatterPanel";
import { MarkdownRenderer } from "@/components/MarkdownRenderer";

import { getEvaluation } from "../actions";

export const dynamic = "force-dynamic";

export default async function EvaluationDetailPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = await params;
  const res = await getEvaluation(id);
  if (res.status !== "ok" || !res.evaluation) {
    notFound();
  }

  const { title, frontmatter, body_markdown, stale } = res.evaluation;
  const category = String(frontmatter.category ?? "");
  const lastVerified = String(frontmatter.last_verified ?? "");

  return (
    <div className="mx-auto max-w-6xl">
      <nav className="mb-4 text-sm text-neutral-500">
        <Link href="/modules/vendor-eval" className="hover:text-neutral-900">
          Vendor &amp; Model Evaluation Center
        </Link>
        <span className="mx-2">/</span>
        <span className="text-neutral-700">{title}</span>
      </nav>

      <header className="mb-6">
        <div className="mb-2 flex flex-wrap items-center gap-2 text-xs">
          {category && (
            <span className="rounded bg-neutral-900 px-2 py-0.5 font-medium capitalize text-white">
              {category.replace(/-/g, " ")}
            </span>
          )}
          {lastVerified && (
            <span className="rounded bg-neutral-100 px-2 py-0.5 text-neutral-700">
              Verified {lastVerified.slice(0, 10)}
            </span>
          )}
          {stale && (
            <span className="inline-flex items-center gap-1 rounded border border-amber-200 bg-amber-100 px-1.5 py-0.5 font-medium uppercase text-amber-700">
              <AlertTriangle className="h-3 w-3" />
              Stale — re-verify
            </span>
          )}
        </div>
        <h1 className="text-2xl font-semibold">{title}</h1>
      </header>

      <div className="flex flex-col gap-8 lg:flex-row">
        <article className="min-w-0 flex-1">
          <MarkdownRenderer>{body_markdown}</MarkdownRenderer>
        </article>
        <aside className="w-full shrink-0 space-y-6 lg:w-72">
          <AssetChatPanelHook
            assetId={res.evaluation.id}
            assetTitle={title}
            assetContent={body_markdown}
            assetFrontmatter={frontmatter}
          />
          <section className="rounded-lg border border-neutral-200 p-4">
            <h2 className="mb-3 text-sm font-semibold">Details</h2>
            <FrontmatterPanel frontmatter={frontmatter} />
          </section>
        </aside>
      </div>
    </div>
  );
}

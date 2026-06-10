import Link from "next/link";
import { notFound } from "next/navigation";

import { AssetChatPanelHook } from "@/components/AssetChatPanelHook";
import { FrontmatterPanel } from "@/components/FrontmatterPanel";
import { MarkdownRenderer } from "@/components/MarkdownRenderer";
import { costLabel } from "@/lib/tools";

import { getTool } from "../actions";

export const dynamic = "force-dynamic";

export default async function ToolDetailPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = await params;
  const res = await getTool(id);
  if (res.status !== "ok" || !res.tool) {
    notFound();
  }

  const { summary, body_markdown, frontmatter } = res.tool;

  return (
    <div className="mx-auto max-w-6xl">
      <nav className="mb-4 text-sm text-neutral-500">
        <Link href="/modules/tools-repo" className="hover:text-neutral-900">
          Skills &amp; Tools Repository
        </Link>
        <span className="mx-2">/</span>
        <span className="text-neutral-700">{summary.name}</span>
      </nav>

      <header className="mb-6">
        <div className="mb-2 flex flex-wrap items-center gap-2 text-xs">
          <span className="rounded bg-neutral-900 px-2 py-0.5 font-medium capitalize text-white">
            {summary.category.replace(/-/g, " ")}
          </span>
          <span className="rounded bg-neutral-100 px-2 py-0.5 text-neutral-700">
            {costLabel(summary.cost_model)}
          </span>
          {summary.ai_stage_fit.length > 0 && (
            <span className="rounded bg-neutral-100 px-2 py-0.5 text-neutral-700">
              Stages {summary.ai_stage_fit.join(", ")}
            </span>
          )}
        </div>
        <h1 className="text-2xl font-semibold">{summary.name}</h1>
        {summary.stack.length > 0 && (
          <p className="mt-1 text-sm capitalize text-neutral-500">{summary.stack.join(" · ")}</p>
        )}
      </header>

      <div className="flex flex-col gap-8 lg:flex-row">
        <article className="min-w-0 flex-1">
          <MarkdownRenderer>{body_markdown}</MarkdownRenderer>
        </article>
        <aside className="w-full shrink-0 space-y-6 lg:w-72">
          <AssetChatPanelHook
            assetId={summary.id}
            assetTitle={summary.name}
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

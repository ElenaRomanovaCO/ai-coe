import Link from "next/link";
import { notFound } from "next/navigation";

import { AssetActions } from "@/components/AssetActions";
import { AssetChatPanelHook } from "@/components/AssetChatPanelHook";
import { FrontmatterPanel } from "@/components/FrontmatterPanel";
import { MarkdownRenderer } from "@/components/MarkdownRenderer";

import { getAsset } from "../actions";

export const dynamic = "force-dynamic";

export default async function AssetDetailPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = await params;
  // Server fetch: asset body + aggregates (no per-user state — that needs the
  // client-side display name, loaded by <AssetActions/>).
  const res = await getAsset(id);
  if (res.status !== "ok" || !res.asset) {
    notFound();
  }

  const { summary, body_markdown, frontmatter } = res.asset;

  return (
    <div className="mx-auto max-w-6xl">
      <nav className="mb-4 text-sm text-neutral-500">
        <Link href="/modules/asset-library" className="hover:text-neutral-900">
          Asset Library
        </Link>
        <span className="mx-2">/</span>
        <span className="text-neutral-700">{summary.title}</span>
      </nav>

      <header className="mb-6">
        <div className="mb-2 flex flex-wrap items-center gap-2">
          <span className="rounded bg-neutral-900 px-2 py-0.5 text-xs font-medium text-white">
            {summary.type}
          </span>
          <span className="rounded bg-neutral-100 px-2 py-0.5 text-xs capitalize text-neutral-700">
            {summary.industry.replace(/-/g, " ")}
          </span>
          <span className="rounded bg-neutral-100 px-2 py-0.5 text-xs text-neutral-700">
            Stage {summary.ai_stage}
          </span>
        </div>
        <h1 className="text-2xl font-semibold">{summary.title}</h1>
      </header>

      <div className="flex flex-col gap-8 lg:flex-row">
        <article className="min-w-0 flex-1">
          <MarkdownRenderer>{body_markdown}</MarkdownRenderer>
        </article>
        <aside className="w-full shrink-0 space-y-6 lg:w-72">
          <AssetChatPanelHook
            assetId={summary.id}
            assetTitle={summary.title}
            assetContent={body_markdown}
            assetFrontmatter={frontmatter}
          />
          <section className="rounded-lg border border-neutral-200 p-4">
            <AssetActions assetId={summary.id} initialAggregates={res.aggregates} />
          </section>
          <section className="rounded-lg border border-neutral-200 p-4">
            <h2 className="mb-3 text-sm font-semibold">Details</h2>
            <FrontmatterPanel frontmatter={frontmatter} />
          </section>
        </aside>
      </div>
    </div>
  );
}

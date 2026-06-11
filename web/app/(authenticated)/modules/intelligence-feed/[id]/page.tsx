import Link from "next/link";
import { notFound } from "next/navigation";
import { ExternalLink } from "lucide-react";

import { AssetChatPanelHook } from "@/components/AssetChatPanelHook";
import { CommentaryCard } from "@/components/feed/CommentaryCard";
import { FrontmatterPanel } from "@/components/FrontmatterPanel";
import { MarkdownRenderer } from "@/components/MarkdownRenderer";
import {
  CATEGORY_STYLE,
  RADAR_STATUS_STYLE,
  categoryLabel,
} from "@/lib/feed";
import { cn } from "@/lib/utils";

import { getFeedItem } from "../actions";

export const dynamic = "force-dynamic";

export default async function FeedItemDetailPage({
  params,
  searchParams,
}: {
  params: Promise<{ id: string }>;
  searchParams: Promise<{ industry?: string; stage?: string }>;
}) {
  const { id } = await params;
  const sp = await searchParams;
  const industry = sp.industry || "cross-industry";
  const stage = Number.isFinite(Number(sp.stage)) ? Number(sp.stage) : 2;

  // Fetch the item pre-tailored to the profile carried from the browse page.
  const res = await getFeedItem(id, { industries: [industry], ai_stage: stage });
  if (res.status !== "ok" || !res.item) {
    notFound();
  }

  const { item, summary, commentary } = res;
  const fm = item.frontmatter ?? {};
  const sourceUrl = String(fm.source_url ?? "");

  return (
    <div className="mx-auto max-w-6xl">
      <nav className="mb-4 text-sm text-neutral-500">
        <Link href="/modules/intelligence-feed" className="hover:text-neutral-900">
          AI Intelligence Feed
        </Link>
        <span className="mx-2">/</span>
        <span className="text-neutral-700">{item.title}</span>
      </nav>

      <header className="mb-6">
        <div className="mb-2 flex flex-wrap items-center gap-2 text-xs">
          {summary.category && (
            <span
              className={cn(
                "rounded border px-1.5 py-0.5 font-medium uppercase",
                CATEGORY_STYLE[summary.category] ?? "border-neutral-200 bg-neutral-100 text-neutral-600",
              )}
            >
              {categoryLabel(summary.category)}
            </span>
          )}
          {summary.radar_status && (
            <span
              className={cn(
                "rounded border px-1.5 py-0.5 font-medium uppercase",
                RADAR_STATUS_STYLE[summary.radar_status] ?? "border-neutral-200 bg-neutral-100 text-neutral-600",
              )}
            >
              {summary.radar_status}
            </span>
          )}
          {summary.published_at && (
            <span className="text-neutral-400">{summary.published_at.slice(0, 10)}</span>
          )}
        </div>
        <h1 className="text-2xl font-semibold">{item.title}</h1>
      </header>

      <div className="flex flex-col gap-8 lg:flex-row">
        <article className="min-w-0 flex-1">
          <CommentaryCard
            itemId={item.id}
            initial={commentary}
            initialIndustry={industry}
            initialStage={stage}
          />
          <MarkdownRenderer>{item.body_markdown}</MarkdownRenderer>
        </article>

        <aside className="w-full shrink-0 space-y-6 lg:w-72">
          <AssetChatPanelHook
            assetId={item.id}
            assetTitle={item.title}
            assetContent={item.body_markdown}
            assetFrontmatter={fm}
          />
          {sourceUrl && (
            <a
              href={sourceUrl}
              target="_blank"
              rel="noopener noreferrer"
              className="flex items-center justify-center gap-2 rounded-lg border border-neutral-200 px-3 py-2 text-sm font-medium text-neutral-700 hover:border-indigo-300 hover:bg-neutral-50"
            >
              <ExternalLink className="h-4 w-4" />
              View source
            </a>
          )}
          <section className="rounded-lg border border-neutral-200 p-4">
            <h2 className="mb-3 text-sm font-semibold">Details</h2>
            <FrontmatterPanel frontmatter={fm} />
          </section>
        </aside>
      </div>
    </div>
  );
}

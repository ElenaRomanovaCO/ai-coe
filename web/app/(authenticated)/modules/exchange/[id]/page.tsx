import Link from "next/link";
import { notFound } from "next/navigation";
import { ExternalLink } from "lucide-react";

import { AssetChatPanelHook } from "@/components/AssetChatPanelHook";
import { FrontmatterPanel } from "@/components/FrontmatterPanel";
import { MarkdownRenderer } from "@/components/MarkdownRenderer";
import {
  CATEGORY_STYLE,
  TOOL_STYLE,
  categoryLabel,
  toolLabel,
} from "@/lib/exchange";
import { cn } from "@/lib/utils";

import { getEntry } from "../actions";

export const dynamic = "force-dynamic";

export default async function ExchangeDetailPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = await params;
  const res = await getEntry(id);
  if (res.status !== "ok" || !res.entry) {
    notFound();
  }

  const e = res.entry;
  const fm = res.frontmatter ?? {};

  return (
    <div className="mx-auto max-w-6xl">
      <nav className="mb-4 text-sm text-neutral-500">
        <Link href="/modules/exchange" className="hover:text-neutral-900">
          Skills &amp; Plugin Exchange
        </Link>
        <span className="mx-2">/</span>
        <span className="text-neutral-700">{e.name}</span>
      </nav>

      <header className="mb-6">
        <div className="mb-2 flex flex-wrap items-center gap-2 text-xs">
          <span
            className={cn(
              "rounded border px-1.5 py-0.5 font-medium",
              TOOL_STYLE[e.tool] ?? "border-neutral-200 bg-neutral-100 text-neutral-600",
            )}
          >
            {toolLabel(e.tool)}
          </span>
          <span
            className={cn(
              "rounded border px-1.5 py-0.5 font-medium",
              CATEGORY_STYLE[e.category] ?? "border-neutral-200 bg-neutral-100 text-neutral-600",
            )}
          >
            {categoryLabel(e.category)}
          </span>
        </div>
        <h1 className="text-2xl font-semibold">{e.name}</h1>
        {e.summary && <p className="mt-1 text-sm text-neutral-500">{e.summary}</p>}
      </header>

      <div className="flex flex-col gap-8 lg:flex-row">
        <article className="min-w-0 flex-1">
          {e.install && (
            <section className="mb-6 rounded-lg border border-neutral-200 bg-neutral-50">
              <h2 className="border-b border-neutral-200 px-4 py-2 text-xs font-semibold uppercase tracking-wide text-neutral-500">
                Install
              </h2>
              <pre className="overflow-x-auto whitespace-pre-wrap px-4 py-3 text-sm text-neutral-800">
                {e.install.trim()}
              </pre>
            </section>
          )}
          <MarkdownRenderer>{e.body_markdown ?? ""}</MarkdownRenderer>
        </article>

        <aside className="w-full shrink-0 space-y-6 lg:w-72">
          <AssetChatPanelHook
            assetId={e.id}
            assetTitle={e.name}
            assetContent={e.body_markdown ?? ""}
            assetFrontmatter={fm}
          />
          {e.source_url && (
            <a
              href={e.source_url}
              target="_blank"
              rel="noopener noreferrer"
              className="flex items-center justify-center gap-2 rounded-lg border border-neutral-200 px-3 py-2 text-sm font-medium text-neutral-700 hover:border-indigo-300 hover:bg-neutral-50"
            >
              <ExternalLink className="h-4 w-4" />
              Source
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

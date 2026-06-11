import Link from "next/link";
import { notFound } from "next/navigation";
import { Download } from "lucide-react";

import { MarkdownRenderer } from "@/components/MarkdownRenderer";

import { getSow } from "../actions";

export const dynamic = "force-dynamic";

export default async function SowResultPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = await params;
  const res = await getSow(id);
  if (res.status !== "ok" || !res.markdown) {
    notFound();
  }

  return (
    <div className="mx-auto max-w-6xl">
      <nav className="mb-4 text-sm text-neutral-500">
        <Link href="/modules/sow-generator" className="hover:text-neutral-900">
          SOW Generator
        </Link>
        <span className="mx-2">/</span>
        <span className="text-neutral-700">{res.title}</span>
      </nav>

      <div className="flex flex-col gap-8 lg:flex-row-reverse">
        <aside className="w-full shrink-0 space-y-4 lg:w-64">
          {res.download_url && (
            <a
              href={res.download_url}
              target="_blank"
              rel="noopener noreferrer"
              className="flex items-center justify-center gap-2 rounded-lg bg-indigo-600 px-3 py-2 text-sm font-medium text-white hover:bg-indigo-700"
            >
              <Download className="h-4 w-4" />
              Export .md
            </a>
          )}
          {res.sections.length > 0 && (
            <nav className="rounded-lg border border-neutral-200 p-4">
              <h2 className="mb-2 text-xs font-semibold uppercase tracking-wide text-neutral-500">
                Sections
              </h2>
              <ol className="space-y-1 text-sm text-neutral-600">
                {res.sections.map((s, i) => (
                  <li key={i}>
                    {i + 1}. {s}
                  </li>
                ))}
              </ol>
            </nav>
          )}
        </aside>

        <article className="min-w-0 flex-1">
          <MarkdownRenderer>{res.markdown}</MarkdownRenderer>
        </article>
      </div>
    </div>
  );
}

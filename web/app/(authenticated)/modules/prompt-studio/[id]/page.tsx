import Link from "next/link";
import { notFound } from "next/navigation";

import { PromptEditor } from "@/components/PromptEditor";

import { getPrompt, versionHistory } from "../actions";

export const dynamic = "force-dynamic";

export default async function PromptEditorPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = await params;
  const res = await getPrompt(id);
  if (res.status !== "ok" || !res.prompt) {
    notFound();
  }
  const history = await versionHistory(id);

  return (
    <div className="mx-auto max-w-6xl">
      <nav className="mb-4 text-sm text-neutral-500">
        <Link href="/modules/prompt-studio" className="hover:text-neutral-900">
          Prompt Studio
        </Link>
        <span className="mx-2">/</span>
        <span className="text-neutral-700">{res.prompt.title}</span>
      </nav>

      <header className="mb-6">
        <div className="mb-1 flex flex-wrap items-center gap-2 text-xs">
          <span
            className={
              res.prompt.source === "seed"
                ? "rounded bg-neutral-100 px-1.5 py-0.5 font-medium uppercase text-neutral-600"
                : "rounded bg-indigo-100 px-1.5 py-0.5 font-medium uppercase text-indigo-700"
            }
          >
            {res.prompt.source}
          </span>
          <span className="rounded bg-neutral-100 px-1.5 py-0.5 text-neutral-600">
            v{res.prompt.version}
          </span>
          {res.prompt.parent_id && (
            <span className="text-neutral-400">forked/versioned from {res.prompt.parent_id}</span>
          )}
        </div>
        <h1 className="text-2xl font-semibold">{res.prompt.title}</h1>
      </header>

      <PromptEditor prompt={res.prompt} history={history.versions ?? []} />
    </div>
  );
}

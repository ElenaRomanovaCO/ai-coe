import Link from "next/link";
import { notFound } from "next/navigation";

import { PromptDiff } from "@/components/PromptDiff";

import { getPrompt } from "../../../actions";

export const dynamic = "force-dynamic";

export default async function PromptDiffPage({
  params,
}: {
  params: Promise<{ id: string; other: string }>;
}) {
  const { id, other } = await params;
  const [base, cmp] = await Promise.all([getPrompt(id), getPrompt(other)]);
  if (base.status !== "ok" || !base.prompt || cmp.status !== "ok" || !cmp.prompt) {
    notFound();
  }

  return (
    <div className="mx-auto max-w-6xl">
      <nav className="mb-4 text-sm text-neutral-500">
        <Link href="/modules/prompt-studio" className="hover:text-neutral-900">
          Prompt Studio
        </Link>
        <span className="mx-2">/</span>
        <Link href={`/modules/prompt-studio/${id}`} className="hover:text-neutral-900">
          {base.prompt.title}
        </Link>
        <span className="mx-2">/</span>
        <span className="text-neutral-700">Diff</span>
      </nav>

      <h1 className="mb-6 text-2xl font-semibold">Compare versions</h1>

      <PromptDiff
        left={{
          id: base.prompt.id,
          title: base.prompt.title,
          version: base.prompt.version,
          prompt_text: base.prompt.prompt_text,
        }}
        right={{
          id: cmp.prompt.id,
          title: cmp.prompt.title,
          version: cmp.prompt.version,
          prompt_text: cmp.prompt.prompt_text,
        }}
      />
    </div>
  );
}

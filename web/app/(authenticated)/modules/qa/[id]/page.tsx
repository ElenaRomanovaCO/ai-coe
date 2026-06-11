import Link from "next/link";
import { notFound } from "next/navigation";

import { AnswerList } from "@/components/qa/AnswerList";

import { getThread } from "../actions";

export const dynamic = "force-dynamic";

export default async function ThreadPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = await params;
  const res = await getThread(id);
  if (res.status !== "ok" || !res.thread) {
    notFound();
  }
  const { thread } = res;

  return (
    <div className="mx-auto max-w-3xl">
      <nav className="mb-4 text-sm text-neutral-500">
        <Link href="/modules/qa" className="hover:text-neutral-900">
          Q&amp;A
        </Link>
        <span className="mx-2">/</span>
        <span className="text-neutral-700">Thread</span>
      </nav>

      <header className="mb-6">
        <h1 className="text-xl font-semibold">{thread.question}</h1>
        <div className="mt-2 flex flex-wrap items-center gap-2 text-xs text-neutral-400">
          <span>asked by {thread.posted_by || "anon"}</span>
          <span>{(thread.posted_at || "").slice(0, 10)}</span>
          {thread.tags.map((t) => (
            <span key={t} className="rounded bg-neutral-100 px-1.5 py-0.5 text-neutral-500">
              {t}
            </span>
          ))}
        </div>
      </header>

      <AnswerList threadId={thread.id} initialAnswers={thread.answers} />
    </div>
  );
}

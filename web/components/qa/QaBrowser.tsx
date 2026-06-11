"use client";

import { useMemo, useState, useSyncExternalStore } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { ArrowBigUp, MessageSquarePlus, Sparkles } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { getDisplayName } from "@/lib/auth";
import { SORT_OPTIONS, type ThreadSummary } from "@/lib/qa";
import { cn } from "@/lib/utils";

import { postThread } from "@/app/(authenticated)/modules/qa/actions";

const SELECT_CLASS =
  "rounded-md border border-neutral-300 bg-white px-3 py-2 text-sm text-neutral-900 focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500";

export function QaBrowser({ threads }: { threads: ThreadSummary[] }) {
  const router = useRouter();
  const name = useSyncExternalStore(
    () => () => {},
    () => getDisplayName(),
    () => null,
  );

  const [sort, setSort] = useState("recent");
  const [tag, setTag] = useState<string | null>(null);
  const [text, setText] = useState("");
  const [composing, setComposing] = useState(false);

  const tags = useMemo(
    () => [...new Set(threads.flatMap((t) => t.tags))].filter(Boolean).sort(),
    [threads],
  );

  const shown = useMemo(() => {
    const q = text.trim().toLowerCase();
    const filtered = threads.filter((t) => {
      if (tag && !t.tags.includes(tag)) return false;
      if (q && !t.question.toLowerCase().includes(q)) return false;
      return true;
    });
    const sorted = [...filtered];
    if (sort === "upvotes") sorted.sort((a, b) => b.score - a.score);
    else if (sort === "unanswered") sorted.sort((a, b) => a.answer_count - b.answer_count);
    else sorted.sort((a, b) => b.posted_at.localeCompare(a.posted_at));
    return sorted;
  }, [threads, tag, text, sort]);

  return (
    <div className="space-y-5">
      <div className="flex flex-wrap items-center gap-2">
        <Input
          placeholder="Search questions…"
          value={text}
          onChange={(e) => setText(e.target.value)}
          className="max-w-xs"
        />
        <select className={SELECT_CLASS} value={sort} onChange={(e) => setSort(e.target.value)}>
          {SORT_OPTIONS.map((o) => (
            <option key={o.value} value={o.value}>
              {o.label}
            </option>
          ))}
        </select>
        <div className="ml-auto flex gap-2">
          <Link href="/modules/qa/ask">
            <Button variant="outline">
              <Sparkles className="h-4 w-4" />
              Ask AI
            </Button>
          </Link>
          <Button onClick={() => setComposing((v) => !v)}>
            <MessageSquarePlus className="h-4 w-4" />
            Post question
          </Button>
        </div>
      </div>

      {tags.length > 0 && (
        <div className="flex flex-wrap gap-1">
          {tags.map((t) => (
            <button
              key={t}
              onClick={() => setTag(tag === t ? null : t)}
              className={cn(
                "rounded-full border px-2 py-0.5 text-xs",
                tag === t
                  ? "border-indigo-600 bg-indigo-600 text-white"
                  : "border-neutral-300 text-neutral-600 hover:border-indigo-400",
              )}
            >
              {t}
            </button>
          ))}
        </div>
      )}

      {composing && (
        <ComposeForm
          name={name}
          onPosted={(id) => router.push(`/modules/qa/${id}`)}
          onCancel={() => setComposing(false)}
        />
      )}

      <p className="text-sm text-neutral-500">
        {shown.length} of {threads.length} questions
      </p>
      {shown.length === 0 ? (
        <p className="mt-8 text-center text-neutral-400">No questions yet — be the first to post.</p>
      ) : (
        <ul className="space-y-3">
          {shown.map((t) => (
            <ThreadCard key={t.id} thread={t} />
          ))}
        </ul>
      )}
    </div>
  );
}

function ThreadCard({ thread: t }: { thread: ThreadSummary }) {
  return (
    <li>
      <Link
        href={`/modules/qa/${t.id}`}
        className="flex items-start gap-4 rounded-lg border border-neutral-200 p-4 transition-colors hover:border-indigo-300 hover:bg-neutral-50"
      >
        <div className="flex w-12 shrink-0 flex-col items-center text-neutral-500">
          <span className="flex items-center gap-0.5 text-sm font-medium">
            <ArrowBigUp className="h-4 w-4" />
            {t.score}
          </span>
          <span className="mt-1 text-[11px]">{t.answer_count} ans</span>
        </div>
        <div className="min-w-0 flex-1">
          <p className="text-sm font-medium text-neutral-900">{t.question}</p>
          <div className="mt-1 flex flex-wrap items-center gap-2 text-xs text-neutral-400">
            <span>{(t.posted_at || "").slice(0, 10)}</span>
            {t.tags.map((tag) => (
              <span key={tag} className="rounded bg-neutral-100 px-1.5 py-0.5 text-neutral-500">
                {tag}
              </span>
            ))}
          </div>
        </div>
      </Link>
    </li>
  );
}

function ComposeForm({
  name,
  onPosted,
  onCancel,
}: {
  name: string | null;
  onPosted: (id: string) => void;
  onCancel: () => void;
}) {
  const [question, setQuestion] = useState("");
  const [tags, setTags] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function onSubmit() {
    if (!name || !question.trim() || submitting) return;
    setSubmitting(true);
    setError(null);
    try {
      const res = await postThread({
        question: question.trim(),
        tags: tags
          .split(",")
          .map((t) => t.trim())
          .filter(Boolean),
        display_name: name,
      });
      if (res.status === "ok" && res.thread?.id) {
        onPosted(res.thread.id);
      } else {
        setError(res.message || "Could not post the question.");
        setSubmitting(false);
      }
    } catch {
      setError("Something went wrong posting. Please try again.");
      setSubmitting(false);
    }
  }

  return (
    <div className="space-y-3 rounded-lg border border-neutral-200 p-4">
      {!name && (
        <p className="text-sm text-neutral-500">
          Set a display name (log out and back in) to post a question.
        </p>
      )}
      <Input
        placeholder="Your question…"
        value={question}
        onChange={(e) => setQuestion(e.target.value)}
      />
      <Input
        placeholder="Tags (comma-separated)"
        value={tags}
        onChange={(e) => setTags(e.target.value)}
      />
      {error && <p className="text-sm text-red-600">{error}</p>}
      <div className="flex gap-2">
        <Button onClick={onSubmit} disabled={!name || !question.trim() || submitting}>
          {submitting ? "Posting…" : "Post"}
        </Button>
        <Button variant="ghost" onClick={onCancel}>
          Cancel
        </Button>
      </div>
    </div>
  );
}

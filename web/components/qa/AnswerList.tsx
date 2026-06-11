"use client";

import { useState, useSyncExternalStore } from "react";
import { ArrowBigUp } from "lucide-react";

import { answerThread, upvote } from "@/app/(authenticated)/modules/qa/actions";
import { Button } from "@/components/ui/button";
import { getDisplayName } from "@/lib/auth";
import type { Answer } from "@/lib/qa";
import { cn } from "@/lib/utils";

const TEXTAREA_CLASS =
  "w-full min-h-24 resize-y rounded-md border border-neutral-300 bg-white px-3 py-2 text-sm text-neutral-900 focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500";

export function AnswerList({
  threadId,
  initialAnswers,
}: {
  threadId: string;
  initialAnswers: Answer[];
}) {
  const name = useSyncExternalStore(
    () => () => {},
    () => getDisplayName(),
    () => null,
  );

  const [answers, setAnswers] = useState<Answer[]>(initialAnswers);
  const [text, setText] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  function resort(list: Answer[]): Answer[] {
    return [...list].sort((a, b) => b.upvotes - a.upvotes);
  }

  async function onUpvote(answerId: string) {
    if (!name) return;
    const current = answers.find((a) => a.id === answerId);
    if (current?.voted) return; // idempotent on the client too
    try {
      const res = await upvote({ thread_id: threadId, answer_id: answerId, display_name: name });
      if (res.status === "ok") {
        setAnswers((prev) =>
          resort(
            prev.map((a) =>
              a.id === answerId ? { ...a, upvotes: res.upvotes, voted: res.voted } : a,
            ),
          ),
        );
      }
    } catch {
      /* non-fatal */
    }
  }

  async function onAnswer() {
    if (!name || !text.trim() || submitting) return;
    setSubmitting(true);
    setError(null);
    try {
      const res = await answerThread({
        thread_id: threadId,
        answer_text: text.trim(),
        display_name: name,
      });
      if (res.status === "ok") {
        const id = `ans-${answers.length + 1}`;
        setAnswers((prev) => [
          ...prev,
          { id, text: text.trim(), posted_by: name, posted_at: "", upvotes: 0, voted: false },
        ]);
        setText("");
      } else {
        setError(res.message || "Could not post the answer.");
      }
    } catch {
      setError("Something went wrong. Please try again.");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="space-y-6">
      <section>
        <h2 className="mb-3 text-sm font-semibold text-neutral-700">
          {answers.length} {answers.length === 1 ? "answer" : "answers"}
        </h2>
        {answers.length === 0 ? (
          <p className="rounded-lg border border-dashed border-neutral-200 p-4 text-sm text-neutral-400">
            No answers yet. Share what you know below.
          </p>
        ) : (
          <ul className="space-y-3">
            {answers.map((a) => (
              <li key={a.id} className="flex items-start gap-3 rounded-lg border border-neutral-200 p-4">
                <button
                  onClick={() => onUpvote(a.id)}
                  disabled={!name || a.voted}
                  className={cn(
                    "flex w-10 shrink-0 flex-col items-center rounded-md py-1 text-neutral-500",
                    a.voted ? "text-indigo-600" : "hover:bg-neutral-100 hover:text-indigo-600",
                    !name && "cursor-not-allowed opacity-50",
                  )}
                  title={name ? "Upvote" : "Set a display name to upvote"}
                >
                  <ArrowBigUp className="h-5 w-5" />
                  <span className="text-sm font-medium">{a.upvotes}</span>
                </button>
                <div className="min-w-0">
                  <p className="whitespace-pre-wrap text-sm text-neutral-800">{a.text}</p>
                  <p className="mt-1 text-xs text-neutral-400">
                    {a.posted_by || "anon"}
                    {a.posted_at ? ` · ${a.posted_at.slice(0, 10)}` : ""}
                  </p>
                </div>
              </li>
            ))}
          </ul>
        )}
      </section>

      <section>
        <h2 className="mb-2 text-sm font-semibold text-neutral-700">Your answer</h2>
        {!name && (
          <p className="mb-2 text-sm text-neutral-500">
            Set a display name (log out and back in) to answer.
          </p>
        )}
        <textarea
          className={TEXTAREA_CLASS}
          value={text}
          onChange={(e) => setText(e.target.value)}
          placeholder="Share what you know…"
        />
        {error && <p className="mt-1 text-sm text-red-600">{error}</p>}
        <Button onClick={onAnswer} disabled={!name || !text.trim() || submitting} className="mt-2">
          {submitting ? "Posting…" : "Post answer"}
        </Button>
      </section>
    </div>
  );
}

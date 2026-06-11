"use client";

import { useRef, useState, useSyncExternalStore } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { FileText, MessageSquarePlus, Sparkles } from "lucide-react";

import {
  answerWithCitations,
  postThread,
} from "@/app/(authenticated)/modules/qa/actions";
import { MarkdownRenderer } from "@/components/MarkdownRenderer";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { getDisplayName } from "@/lib/auth";
import { CONFIDENCE_STYLE, SUGGESTED_QUESTIONS, type AnswerResult } from "@/lib/qa";
import { cn } from "@/lib/utils";

// AI mode: ask a natural-language question, get a synthesized answer with citations
// from across the Knowledge Base, then optionally save it as a community thread.
export function AiAsk() {
  const router = useRouter();
  const name = useSyncExternalStore(
    () => () => {},
    () => getDisplayName(),
    () => null,
  );

  const inputRef = useRef<HTMLInputElement>(null);
  const [question, setQuestion] = useState("");
  const [asking, setAsking] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<AnswerResult | null>(null);
  const [saving, setSaving] = useState(false);

  // Fill the box from a starter question and select the [bracket] so the user can
  // type their topic right over it.
  function pickSuggestion(q: string) {
    setQuestion(q);
    const m = q.match(/\[[^\]]*\]/);
    requestAnimationFrame(() => {
      const el = inputRef.current;
      if (!el) return;
      el.focus();
      if (m && m.index != null) el.setSelectionRange(m.index, m.index + m[0].length);
      else el.setSelectionRange(q.length, q.length);
    });
  }

  async function onAsk() {
    if (!question.trim() || asking) return;
    setAsking(true);
    setError(null);
    setResult(null);
    try {
      const res = await answerWithCitations({ question: question.trim() });
      if (res.status === "ok") {
        setResult(res);
      } else {
        setError(res.message || "Could not answer that question.");
      }
    } catch {
      setError("Something went wrong. Please try again.");
    } finally {
      setAsking(false);
    }
  }

  async function onSaveThread() {
    if (!name || !result || saving) return;
    setSaving(true);
    try {
      const res = await postThread({
        question: question.trim(),
        tags: [],
        display_name: name,
        initial_answer: result.answer,
      });
      if (res.status === "ok" && res.thread?.id) {
        router.push(`/modules/qa/${res.thread.id}`);
      } else {
        setSaving(false);
      }
    } catch {
      setSaving(false);
    }
  }

  return (
    <div className="space-y-5">
      <div className="flex flex-wrap items-center gap-2">
        <Input
          ref={inputRef}
          placeholder="Ask anything about the Knowledge Base…"
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && onAsk()}
          className="min-w-0 flex-1"
        />
        <Button onClick={onAsk} disabled={asking || !question.trim()}>
          <Sparkles className="h-4 w-4" />
          {asking ? "Thinking…" : "Ask"}
        </Button>
      </div>

      {!result && !asking && (
        <div>
          <p className="mb-2 text-xs font-medium uppercase tracking-wide text-neutral-400">
            Try one of these
          </p>
          <div className="flex flex-wrap gap-2">
            {SUGGESTED_QUESTIONS.map((q) => (
              <button
                key={q}
                type="button"
                onClick={() => pickSuggestion(q)}
                className="rounded-full border border-neutral-300 px-3 py-1 text-sm text-neutral-600 transition-colors hover:border-indigo-400 hover:text-indigo-700"
              >
                {q}
              </button>
            ))}
          </div>
        </div>
      )}

      {error && <p className="text-sm text-red-600">{error}</p>}

      {result && (
        <div className="space-y-4">
          <div className="rounded-lg border border-neutral-200 p-4">
            <div className="mb-3 flex items-center gap-2">
              <span className="text-sm font-semibold">Answer</span>
              <span
                className={cn(
                  "rounded border px-1.5 py-0.5 text-[10px] font-medium uppercase",
                  CONFIDENCE_STYLE[result.confidence],
                )}
              >
                {result.confidence} confidence
              </span>
            </div>
            <MarkdownRenderer>{result.answer}</MarkdownRenderer>
          </div>

          {result.citations.length > 0 && (
            <div>
              <h3 className="mb-2 text-xs font-semibold uppercase tracking-wide text-neutral-500">
                Citations
              </h3>
              <ul className="space-y-2">
                {result.citations.map((c) => (
                  <li key={c.file_path}>
                    <CitationRow
                      title={c.title}
                      contentType={c.content_type}
                      url={c.url}
                    />
                  </li>
                ))}
              </ul>
            </div>
          )}

          {result.related_threads.length > 0 && (
            <div>
              <h3 className="mb-2 text-xs font-semibold uppercase tracking-wide text-neutral-500">
                Related threads
              </h3>
              <ul className="space-y-1 text-sm">
                {result.related_threads.map((r) => (
                  <li key={r.id}>
                    <Link
                      href={r.url ?? `/modules/qa/${r.id}`}
                      className="text-indigo-600 hover:underline"
                    >
                      {r.question}
                    </Link>
                  </li>
                ))}
              </ul>
            </div>
          )}

          <div>
            <Button variant="outline" onClick={onSaveThread} disabled={!name || saving}>
              <MessageSquarePlus className="h-4 w-4" />
              {saving ? "Saving…" : "Save as community thread"}
            </Button>
            {!name && (
              <span className="ml-2 text-xs text-neutral-400">
                Set a display name to save.
              </span>
            )}
          </div>
        </div>
      )}
    </div>
  );
}

function CitationRow({
  title,
  contentType,
  url,
}: {
  title: string;
  contentType: string;
  url: string | null;
}) {
  const inner = (
    <span className="flex items-center gap-2">
      <FileText className="h-4 w-4 shrink-0 text-neutral-400" />
      <span className="min-w-0 truncate text-sm text-neutral-800">{title}</span>
      <span className="shrink-0 rounded bg-neutral-100 px-1.5 py-0.5 text-[10px] uppercase text-neutral-500">
        {contentType}
      </span>
    </span>
  );
  return url ? (
    <Link href={url} className="block rounded-md p-1 hover:bg-neutral-50">
      {inner}
    </Link>
  ) : (
    <div className="p-1">{inner}</div>
  );
}

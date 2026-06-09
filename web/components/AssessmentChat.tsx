"use client";

import { useEffect, useRef, useState } from "react";

import { answerAssessment } from "@/app/(authenticated)/modules/maturity-assessment/actions";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import type { AssessmentResult } from "@/lib/assessment";
import { cn } from "@/lib/utils";

interface Turn {
  role: "question" | "answer";
  text: string;
}

// Conversational in-progress assessment. The adaptive flow runs 8-12 questions;
// each answer round-trips to AGENT-02 and returns the next question or the result.
export function AssessmentChat({
  assessmentId,
  firstQuestion,
  onComplete,
}: {
  assessmentId: string;
  firstQuestion: string;
  onComplete: (result: AssessmentResult) => void;
}) {
  const [turns, setTurns] = useState<Turn[]>([{ role: "question", text: firstQuestion }]);
  const [current, setCurrent] = useState(firstQuestion);
  const [input, setInput] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const scrollRef = useRef<HTMLDivElement | null>(null);

  const answered = turns.filter((t) => t.role === "answer").length;

  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: "smooth" });
  }, [turns]);

  async function submit() {
    const answer = input.trim();
    if (!answer || busy) return;
    setInput("");
    setError(null);
    setTurns((t) => [...t, { role: "answer", text: answer }]);
    setBusy(true);
    try {
      const res = await answerAssessment(assessmentId, answer);
      if (res.status !== "ok") {
        setError("Something went wrong scoring that answer. Please try again.");
        return;
      }
      if (res.is_complete && res.result) {
        onComplete(res.result);
        return;
      }
      if (res.next_question) {
        setCurrent(res.next_question);
        setTurns((t) => [...t, { role: "question", text: res.next_question! }]);
      }
    } catch {
      setError("The assessment service is unavailable. Please try again.");
    } finally {
      setBusy(false);
    }
  }

  // Progress: the flow lands between 8 and 12 questions; show progress toward ~10.
  const pct = Math.min(100, Math.round((answered / 10) * 100));

  return (
    <div className="flex flex-col gap-4">
      <div>
        <div className="mb-1 flex justify-between text-xs text-slate-500">
          <span>{answered} answered</span>
          <span>~8–12 questions</span>
        </div>
        <div className="h-1.5 w-full overflow-hidden rounded-full bg-slate-200">
          <div className="h-full rounded-full bg-indigo-600 transition-all" style={{ width: `${pct}%` }} />
        </div>
      </div>

      <div
        ref={scrollRef}
        className="max-h-[28rem] space-y-3 overflow-y-auto rounded-lg border border-slate-200 bg-slate-50 p-4"
      >
        {turns.map((t, i) => (
          <div key={i} className={cn("flex", t.role === "answer" ? "justify-end" : "justify-start")}>
            <div
              className={cn(
                "max-w-[85%] rounded-lg px-3 py-2 text-sm",
                t.role === "answer"
                  ? "bg-indigo-600 text-white"
                  : "border border-slate-200 bg-white text-slate-800",
              )}
            >
              {t.text}
            </div>
          </div>
        ))}
        {busy && <p className="text-xs text-slate-400">Thinking…</p>}
      </div>

      {error && <p className="text-sm text-red-600">{error}</p>}

      <form
        className="flex items-center gap-2"
        onSubmit={(e) => {
          e.preventDefault();
          void submit();
        }}
      >
        <Input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Type your answer…"
          disabled={busy}
          autoFocus
          aria-label="Your answer"
        />
        <Button
          type="submit"
          disabled={busy || !input.trim()}
          className="bg-indigo-600 hover:bg-indigo-700"
        >
          Send
        </Button>
      </form>
      <p className="text-xs text-slate-400">Current question: {current}</p>
    </div>
  );
}

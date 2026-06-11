"use client";

import { useState, useTransition } from "react";
import { Sparkles } from "lucide-react";

import { getFeedItem } from "@/app/(authenticated)/modules/intelligence-feed/actions";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { AI_STAGES, FEED_INDUSTRIES, type FeedCommentary } from "@/lib/feed";

// WORKER-11's "what this means for you" note, regenerable for a different profile.
// Seeded server-side with the profile carried from the browse page (query params),
// then re-tailored client-side via the getFeedItem server action.
export function CommentaryCard({
  itemId,
  initial,
  initialIndustry,
  initialStage,
}: {
  itemId: string;
  initial: FeedCommentary;
  initialIndustry: string;
  initialStage: number;
}) {
  const [commentary, setCommentary] = useState<FeedCommentary>(initial);
  const [industry, setIndustry] = useState(initialIndustry);
  const [stage, setStage] = useState(initialStage);
  const [pending, startTransition] = useTransition();

  function retailor(nextIndustry: string, nextStage: number) {
    startTransition(async () => {
      const res = await getFeedItem(itemId, {
        industries: [nextIndustry],
        ai_stage: nextStage,
      });
      if (res.status === "ok") setCommentary(res.commentary);
    });
  }

  return (
    <Card className="mb-6 border-indigo-100">
      <CardHeader>
        <CardTitle className="flex items-center gap-2 text-base">
          <Sparkles className="h-4 w-4 text-indigo-600" />
          What this means for you
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="flex flex-wrap items-center gap-2 text-xs">
          <span className="text-neutral-500">Tailored for</span>
          <select
            value={industry}
            onChange={(e) => {
              setIndustry(e.target.value);
              retailor(e.target.value, stage);
            }}
            className="rounded border border-neutral-300 bg-white px-2 py-1 capitalize"
          >
            {FEED_INDUSTRIES.map((i) => (
              <option key={i} value={i}>
                {i.replace(/-/g, " ")}
              </option>
            ))}
          </select>
          <select
            value={stage}
            onChange={(e) => {
              const s = Number(e.target.value);
              setStage(s);
              retailor(industry, s);
            }}
            className="rounded border border-neutral-300 bg-white px-2 py-1"
          >
            {AI_STAGES.map((s) => (
              <option key={s} value={s}>
                Stage {s}
              </option>
            ))}
          </select>
          {pending && <span className="text-indigo-500">tailoring…</span>}
          {!commentary.tailored && !pending && (
            <span className="text-neutral-400">(offline note)</span>
          )}
        </div>
        <p className={`whitespace-pre-wrap text-sm leading-relaxed text-neutral-700 ${pending ? "opacity-60" : ""}`}>
          {commentary.commentary || "No commentary available for this item."}
        </p>
      </CardContent>
    </Card>
  );
}

"use client";

import { useState, useTransition } from "react";
import { useRouter } from "next/navigation";

import { Button } from "@/components/ui/button";
import { UPDATE_TYPES, type UpdateType } from "@/lib/health";

// Posts an update for one engagement; on success refreshes the server component so the
// new (analyzed) entry appears in the timeline with its flags.
export function PostUpdateForm({ engagementId }: { engagementId: string }) {
  const router = useRouter();
  const [text, setText] = useState("");
  const [type, setType] = useState<UpdateType>("status");
  const [error, setError] = useState<string | null>(null);
  const [pending, startTransition] = useTransition();

  function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    if (!text.trim()) return;
    startTransition(async () => {
      const { postUpdate } = await import("@/app/(authenticated)/modules/project-health/actions");
      const res = await postUpdate({
        engagement_id: engagementId,
        update_text: text.trim(),
        update_type: type,
      });
      if (res.status === "ok") {
        setText("");
        router.refresh();
      } else {
        setError(res.message || "Couldn't post the update. Please try again.");
      }
    });
  }

  return (
    <form onSubmit={onSubmit} className="space-y-3 rounded-lg border border-neutral-200 p-4">
      <div className="flex items-center justify-between gap-2">
        <h2 className="text-sm font-semibold">Post an update</h2>
        <select
          value={type}
          onChange={(e) => setType(e.target.value as UpdateType)}
          className="rounded border border-neutral-300 bg-white px-2 py-1 text-xs capitalize"
        >
          {UPDATE_TYPES.map((t) => (
            <option key={t} value={t}>
              {t.replace(/-/g, " ")}
            </option>
          ))}
        </select>
      </div>
      <textarea
        value={text}
        onChange={(e) => setText(e.target.value)}
        placeholder="What happened this week? Scope changes, blockers, decisions…"
        rows={3}
        className="w-full rounded-md border border-neutral-300 bg-transparent px-3 py-2 text-sm placeholder:text-neutral-400"
      />
      {error && <p className="text-sm text-red-600">{error}</p>}
      <Button
        type="submit"
        size="sm"
        disabled={pending || !text.trim()}
        className="bg-indigo-600 hover:bg-indigo-700"
      >
        {pending ? "Analyzing…" : "Post & analyze"}
      </Button>
    </form>
  );
}

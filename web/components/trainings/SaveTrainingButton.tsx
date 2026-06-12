"use client";

import { useState, useSyncExternalStore } from "react";
import { BookmarkCheck, BookmarkPlus, Loader2 } from "lucide-react";

import { getDisplayName } from "@/lib/auth";
import { cn } from "@/lib/utils";

import { saveTraining } from "@/app/(authenticated)/modules/trainings/actions";

export function SaveTrainingButton({
  trainingId,
  initialSaved,
}: {
  trainingId: string;
  initialSaved: boolean;
}) {
  const name = useSyncExternalStore(
    () => () => {},
    () => getDisplayName(),
    () => null,
  );
  const [saved, setSaved] = useState(initialSaved);
  const [busy, setBusy] = useState(false);

  async function onClick() {
    if (!name) return;
    setBusy(true);
    try {
      const res = await saveTraining(name, trainingId, saved);
      if (res.status === "ok") setSaved(res.saved);
    } finally {
      setBusy(false);
    }
  }

  return (
    <button
      onClick={onClick}
      disabled={!name || busy}
      title={name ? undefined : "Set a display name to save"}
      className={cn(
        "inline-flex items-center gap-2 rounded-md border px-3 py-2 text-sm font-medium transition disabled:opacity-50",
        saved
          ? "border-green-300 bg-green-50 text-green-700"
          : "border-slate-300 text-slate-700 hover:bg-slate-50",
      )}
    >
      {busy ? (
        <Loader2 className="h-4 w-4 animate-spin" />
      ) : saved ? (
        <BookmarkCheck className="h-4 w-4" />
      ) : (
        <BookmarkPlus className="h-4 w-4" />
      )}
      {saved ? "Saved" : "Save"}
    </button>
  );
}

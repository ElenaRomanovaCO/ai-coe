"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { Loader2 } from "lucide-react";

import { generateReport } from "@/app/(authenticated)/modules/reports/actions";

// Entry point from the assessment result page: turn this completed assessment into a
// client report and jump straight into the editor.
export function GenerateReportButton({ assessmentId }: { assessmentId: string }) {
  const router = useRouter();
  const [busy, setBusy] = useState(false);

  async function onClick() {
    setBusy(true);
    try {
      const res = await generateReport(assessmentId);
      if (res.status === "ok") {
        router.push(`/modules/reports/${res.report_id}`);
      } else {
        setBusy(false);
      }
    } catch {
      setBusy(false);
    }
  }

  return (
    <button
      onClick={onClick}
      disabled={busy}
      className="flex w-full items-center justify-center gap-2 rounded-md border border-slate-300 px-3 py-2 text-sm font-medium text-slate-700 hover:bg-slate-50 disabled:opacity-50"
    >
      {busy && <Loader2 className="h-4 w-4 animate-spin" />}
      {busy ? "Generating…" : "Generate client report"}
    </button>
  );
}

"use client";

import { useState, useTransition } from "react";
import { Download } from "lucide-react";

import { Button } from "@/components/ui/button";
import { exportBenchmark } from "@/app/(authenticated)/modules/benchmark/actions";

// Persists the slide to the vault (export op) then downloads the markdown client-side.
// Falls back to the already-rendered markdown if the export call fails.
export function BenchmarkExportButton({
  assessmentId,
  markdown,
}: {
  assessmentId: string;
  markdown: string;
}) {
  const [pending, start] = useTransition();
  const [done, setDone] = useState(false);

  function download(md: string) {
    const blob = new Blob([md], { type: "text/markdown" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `benchmark-${assessmentId}.md`;
    a.click();
    URL.revokeObjectURL(url);
  }

  function onExport() {
    setDone(false);
    start(async () => {
      const res = await exportBenchmark(assessmentId);
      download(res.status === "ok" && res.markdown ? res.markdown : markdown);
      setDone(true);
    });
  }

  return (
    <div>
      <Button onClick={onExport} disabled={pending} className="w-full bg-indigo-600 hover:bg-indigo-700">
        <Download className="h-4 w-4" />
        {pending ? "Exporting…" : "Export slide (.md)"}
      </Button>
      {done && <p className="mt-1 text-center text-xs text-green-700">Saved &amp; downloaded.</p>}
    </div>
  );
}

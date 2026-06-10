"use client";

import { Download, X } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import type { KitFile } from "@/lib/kit";

// Right pane — the "kit canvas": the current list of included files (grouped by
// category, removable) + count + export-to-zip.
export function KitPreview({
  kitSlug,
  files,
  onRemove,
  onExport,
  generating,
  downloadUrl,
}: {
  kitSlug: string;
  files: KitFile[];
  onRemove: (sourcePath: string) => void;
  onExport: () => void;
  generating: boolean;
  downloadUrl: string | null;
}) {
  const categories = [...new Set(files.map((f) => f.category))];

  return (
    <Card className="h-full">
      <CardHeader className="flex-row items-center justify-between">
        <CardTitle>Your kit {kitSlug && <span className="font-mono text-xs text-slate-400">/ {kitSlug}</span>}</CardTitle>
        <span className="rounded-full bg-indigo-50 px-2 py-0.5 text-xs font-medium text-indigo-700">
          {files.length} files
        </span>
      </CardHeader>
      <CardContent className="space-y-4">
        {files.length === 0 ? (
          <p className="text-sm text-slate-400">
            No files yet. Set the engagement context and add suggestions.
          </p>
        ) : (
          categories.map((cat) => (
            <div key={cat}>
              <h4 className="mb-1 text-xs font-medium uppercase tracking-wide text-slate-500">
                {cat}
              </h4>
              <ul className="space-y-1">
                {files
                  .filter((f) => f.category === cat)
                  .map((f) => (
                    <li
                      key={f.source_path}
                      className="flex items-center justify-between gap-2 rounded-md border border-slate-200 px-2.5 py-1.5"
                    >
                      <span className="truncate text-sm text-slate-700">{f.title}</span>
                      <button
                        onClick={() => onRemove(f.source_path)}
                        aria-label={`Remove ${f.title}`}
                        className="shrink-0 text-slate-400 hover:text-red-600"
                      >
                        <X className="h-4 w-4" />
                      </button>
                    </li>
                  ))}
              </ul>
            </div>
          ))
        )}

        <div className="border-t border-slate-200 pt-4">
          {downloadUrl ? (
            <a
              href={downloadUrl}
              className="inline-flex w-full items-center justify-center gap-2 rounded-md bg-green-600 px-4 py-2 text-sm font-medium text-white hover:bg-green-700"
            >
              <Download className="h-4 w-4" /> Download kit (.zip)
            </a>
          ) : (
            <Button
              onClick={onExport}
              disabled={generating || files.length === 0}
              className="w-full bg-indigo-600 hover:bg-indigo-700"
            >
              {generating ? "Building zip…" : "Export kit (.zip)"}
            </Button>
          )}
        </div>
      </CardContent>
    </Card>
  );
}

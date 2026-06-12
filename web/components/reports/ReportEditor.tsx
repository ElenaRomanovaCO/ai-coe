"use client";

import { useMemo, useState } from "react";
import { Check, Download, Loader2 } from "lucide-react";

import { Button } from "@/components/ui/button";
import { getDisplayName } from "@/lib/auth";
import {
  isListSection,
  type ReportData,
  type SectionValue,
  sectionToText,
} from "@/lib/reports";

import { updateSection } from "@/app/(authenticated)/modules/reports/actions";

function toValue(key: string, text: string): SectionValue {
  if (isListSection(key)) {
    return text
      .split("\n")
      .map((l) => l.trim())
      .filter(Boolean);
  }
  return text.trim();
}

export function ReportEditor({ report }: { report: ReportData }) {
  const [sections, setSections] = useState<Record<string, SectionValue>>(report.sections);
  const [drafts, setDrafts] = useState<Record<string, string>>(() =>
    Object.fromEntries(report.section_order.map((k) => [k, sectionToText(report.sections[k])])),
  );
  const [savingKey, setSavingKey] = useState<string | null>(null);
  const [savedKey, setSavedKey] = useState<string | null>(null);
  const [exporting, setExporting] = useState(false);

  const order = report.section_order;
  const titles = report.section_titles;

  const dirty = useMemo(() => {
    const d: Record<string, boolean> = {};
    for (const k of order) d[k] = drafts[k] !== sectionToText(sections[k]);
    return d;
  }, [drafts, sections, order]);

  async function onSave(key: string) {
    setSavingKey(key);
    setSavedKey(null);
    try {
      const res = await updateSection(report.report_id, key, toValue(key, drafts[key]));
      if (res.status === "ok") {
        setSections(res.sections);
        setDrafts((d) => ({ ...d, [key]: sectionToText(res.sections[key]) }));
        setSavedKey(key);
      }
    } finally {
      setSavingKey(null);
    }
  }

  async function onExport() {
    setExporting(true);
    try {
      const { downloadReportPdf } = await import("@/lib/reportPdf");
      await downloadReportPdf({
        report_id: report.report_id,
        title: report.title,
        preparedFor: getDisplayName() ?? "",
        sections,
        section_order: order,
        section_titles: titles,
      });
    } finally {
      setExporting(false);
    }
  }

  return (
    <div>
      <div className="mb-4 flex items-center justify-between gap-4">
        <div className="min-w-0">
          <h1 className="truncate text-2xl font-semibold">{report.title}</h1>
          <p className="mt-0.5 text-xs text-slate-500">
            Edit any section, then export to PDF. Changes save to the report.
          </p>
        </div>
        <Button
          onClick={onExport}
          disabled={exporting}
          className="shrink-0 bg-indigo-600 hover:bg-indigo-700"
        >
          {exporting ? (
            <Loader2 className="mr-2 h-4 w-4 animate-spin" />
          ) : (
            <Download className="mr-2 h-4 w-4" />
          )}
          Export PDF
        </Button>
      </div>

      <div className="flex flex-col gap-8 lg:flex-row">
        {/* Editor pane */}
        <div className="min-w-0 flex-1 space-y-5">
          {order.map((key) => (
            <div key={key} className="rounded-lg border border-slate-200 p-4">
              <div className="mb-2 flex items-center justify-between">
                <label className="text-sm font-semibold text-slate-800">{titles[key]}</label>
                <button
                  onClick={() => onSave(key)}
                  disabled={!dirty[key] || savingKey === key}
                  className="flex items-center gap-1 text-xs font-medium text-indigo-600 hover:text-indigo-800 disabled:text-slate-300"
                >
                  {savingKey === key ? (
                    <Loader2 className="h-3 w-3 animate-spin" />
                  ) : savedKey === key && !dirty[key] ? (
                    <Check className="h-3 w-3" />
                  ) : null}
                  {savingKey === key ? "Saving…" : savedKey === key && !dirty[key] ? "Saved" : "Save"}
                </button>
              </div>
              {isListSection(key) && (
                <p className="mb-1 text-[11px] text-slate-400">One item per line.</p>
              )}
              <textarea
                value={drafts[key] ?? ""}
                onChange={(e) => setDrafts((d) => ({ ...d, [key]: e.target.value }))}
                rows={isListSection(key) ? 5 : 4}
                className="w-full resize-y rounded-md border border-slate-200 px-3 py-2 text-sm text-slate-700 focus:border-indigo-400 focus:outline-none focus:ring-1 focus:ring-indigo-400"
              />
            </div>
          ))}
        </div>

        {/* Live preview pane */}
        <aside className="w-full shrink-0 lg:w-[26rem]">
          <div className="sticky top-4 max-h-[80vh] overflow-y-auto rounded-lg border border-slate-200 bg-white p-6 shadow-sm">
            <div className="mb-1 text-[10px] font-semibold uppercase tracking-wide text-slate-400">
              Preview
            </div>
            <h2 className="mb-4 border-b border-slate-100 pb-3 text-lg font-bold text-slate-900">
              {report.title}
            </h2>
            {order.map((key) => {
              const value = sections[key];
              return (
                <section key={key} className="mb-4">
                  <h3 className="mb-1 text-sm font-semibold text-indigo-700">{titles[key]}</h3>
                  {isListSection(key) ? (
                    <ul className="list-disc space-y-0.5 pl-5 text-sm leading-relaxed text-slate-700">
                      {(Array.isArray(value) ? value : []).map((item, i) => (
                        <li key={i}>{item}</li>
                      ))}
                    </ul>
                  ) : (
                    <p className="whitespace-pre-wrap text-sm leading-relaxed text-slate-700">
                      {typeof value === "string" ? value : ""}
                    </p>
                  )}
                </section>
              );
            })}
          </div>
        </aside>
      </div>
    </div>
  );
}

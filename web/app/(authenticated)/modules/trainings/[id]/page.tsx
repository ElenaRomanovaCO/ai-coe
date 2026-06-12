import Link from "next/link";
import { notFound } from "next/navigation";
import { CalendarDays, Clock, ExternalLink, User } from "lucide-react";

import { MarkdownRenderer } from "@/components/MarkdownRenderer";
import { SaveTrainingButton } from "@/components/trainings/SaveTrainingButton";
import { formatDuration } from "@/lib/trainings";

import { getTraining } from "../actions";

export const dynamic = "force-dynamic";

function formatDate(iso: string): string {
  if (!iso) return "";
  const d = new Date(iso);
  return isNaN(d.getTime())
    ? iso
    : d.toLocaleDateString(undefined, { year: "numeric", month: "long", day: "numeric" });
}

export default async function TrainingDetailPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = await params;
  const res = await getTraining(id);
  if (res.status !== "ok" || !res.training) notFound();
  const t = res.training;
  const hosted = t.kind === "hosted";

  return (
    <div className="mx-auto max-w-3xl">
      <nav className="mb-4 text-sm text-slate-500">
        <Link href="/modules/trainings" className="hover:text-slate-900">
          Trainings
        </Link>
        <span className="mx-2">/</span>
        <span className="text-slate-700">{hosted ? "Hosted" : "Tutorial"}</span>
      </nav>

      <h1 className="text-2xl font-semibold text-slate-900">{t.title}</h1>

      {/* Badge row */}
      <div className="mt-3 flex flex-wrap items-center gap-2 text-xs">
        <span
          className={
            hosted
              ? "rounded bg-amber-100 px-2 py-0.5 font-medium text-amber-800"
              : "rounded bg-slate-100 px-2 py-0.5 font-medium text-slate-600"
          }
        >
          {t.source}
        </span>
        <span className="rounded bg-indigo-50 px-2 py-0.5 font-medium text-indigo-700">{t.theme}</span>
        <span className="capitalize text-slate-500">{t.level}</span>
        {t.duration_min > 0 && (
          <span className="flex items-center gap-1 text-slate-500">
            <Clock className="h-3 w-3" /> {formatDuration(t.duration_min)}
          </span>
        )}
      </div>

      {/* Actions */}
      <div className="mt-5 flex flex-wrap items-center gap-3">
        <a
          href={t.url}
          target="_blank"
          rel="noopener noreferrer"
          className="inline-flex items-center gap-2 rounded-md bg-indigo-600 px-4 py-2 text-sm font-medium text-white hover:bg-indigo-700"
        >
          {hosted ? "Watch recording" : "Open course"}
          <ExternalLink className="h-4 w-4" />
        </a>
        <SaveTrainingButton trainingId={t.id} initialSaved={!!t.saved} />
      </div>

      {/* Hosted meta */}
      {hosted && (t.presenter || t.session_date) && (
        <div className="mt-5 flex flex-wrap gap-4 rounded-lg border border-slate-200 bg-slate-50/60 p-4 text-sm text-slate-600">
          {t.presenter && (
            <span className="flex items-center gap-1.5">
              <User className="h-4 w-4 text-slate-400" /> {t.presenter}
            </span>
          )}
          {t.session_date && (
            <span className="flex items-center gap-1.5">
              <CalendarDays className="h-4 w-4 text-slate-400" /> {formatDate(t.session_date)}
            </span>
          )}
        </div>
      )}

      {/* Summary body */}
      <article className="mt-6">
        <MarkdownRenderer>{t.body_markdown || t.summary}</MarkdownRenderer>
      </article>

      {/* Materials (hosted) */}
      {hosted && t.materials.length > 0 && (
        <div className="mt-6">
          <h2 className="mb-2 text-sm font-semibold text-slate-800">Materials</h2>
          <ul className="space-y-1">
            {t.materials.map((m, i) => (
              <li key={i}>
                <a
                  href={m.url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="inline-flex items-center gap-1 text-sm text-indigo-600 hover:underline"
                >
                  {m.label}
                  <ExternalLink className="h-3 w-3" />
                </a>
              </li>
            ))}
          </ul>
        </div>
      )}

      {t.last_verified && (
        <p className="mt-8 border-t border-slate-100 pt-4 text-xs text-slate-400">
          Last verified {formatDate(t.last_verified)}
        </p>
      )}
    </div>
  );
}

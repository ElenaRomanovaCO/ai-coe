import Link from "next/link";
import { notFound } from "next/navigation";

import { PostUpdateForm } from "@/components/health/PostUpdateForm";
import {
  BAND_STYLE,
  SEVERITY_STYLE,
  bandLabel,
  type EngagementUpdate,
  type HealthFlag,
} from "@/lib/health";
import { cn } from "@/lib/utils";

import { getEngagement } from "../actions";

export const dynamic = "force-dynamic";

export default async function EngagementDetailPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = await params;
  const res = await getEngagement(id);
  if (res.status !== "ok" || !res.engagement) {
    notFound();
  }

  const e = res.engagement;

  return (
    <div className="mx-auto max-w-6xl">
      <nav className="mb-4 text-sm text-neutral-500">
        <Link href="/modules/project-health" className="hover:text-neutral-900">
          Project Health
        </Link>
        <span className="mx-2">/</span>
        <span className="text-neutral-700">{e.name}</span>
      </nav>

      <header className="mb-6 flex flex-wrap items-start justify-between gap-3">
        <div>
          <h1 className="text-2xl font-semibold">{e.name}</h1>
          <p className="mt-1 text-sm capitalize text-neutral-500">
            {e.industry ? e.industry.replace(/-/g, " ") : "—"} · Stage {e.ai_stage}
            {e.start_date && <> · started {e.start_date}</>}
          </p>
          {e.use_cases.length > 0 && (
            <div className="mt-2 flex flex-wrap gap-1.5">
              {e.use_cases.map((u) => (
                <span key={u} className="rounded-full bg-neutral-100 px-2 py-0.5 text-xs text-neutral-600">
                  {u}
                </span>
              ))}
            </div>
          )}
        </div>
        <span
          className={cn(
            "rounded border px-3 py-1 text-sm font-medium",
            BAND_STYLE[e.band],
          )}
        >
          {bandLabel(e.band)} · risk {e.risk_score}/100
        </span>
      </header>

      <div className="flex flex-col gap-8 lg:flex-row">
        <div className="min-w-0 flex-1">
          <h2 className="mb-3 text-sm font-semibold uppercase tracking-wide text-neutral-500">
            Update timeline
          </h2>
          {e.updates.length === 0 ? (
            <p className="text-sm text-neutral-400">No updates yet. Post one to analyze health.</p>
          ) : (
            <ol className="space-y-4">
              {e.updates.map((u, i) => (
                <UpdateItem key={i} update={u} />
              ))}
            </ol>
          )}
        </div>

        <aside className="w-full shrink-0 lg:w-80">
          <PostUpdateForm engagementId={e.engagement_id} />
        </aside>
      </div>
    </div>
  );
}

function UpdateItem({ update: u }: { update: EngagementUpdate }) {
  return (
    <li className="rounded-lg border border-neutral-200 p-4">
      <div className="mb-1.5 flex flex-wrap items-center gap-2 text-xs">
        <span className="rounded bg-neutral-900 px-1.5 py-0.5 font-medium uppercase text-white">
          {u.update_type.replace(/-/g, " ")}
        </span>
        <span className="text-neutral-400">{u.ts.slice(0, 16).replace("T", " ")}</span>
        <span className="ml-auto text-neutral-500">risk {u.risk_score}/100</span>
      </div>
      <p className="whitespace-pre-wrap text-sm text-neutral-800">{u.text}</p>
      {u.summary && <p className="mt-2 text-xs italic text-neutral-500">{u.summary}</p>}
      {u.flags.length > 0 && (
        <ul className="mt-3 space-y-2">
          {u.flags.map((f, i) => (
            <FlagItem key={i} flag={f} />
          ))}
        </ul>
      )}
    </li>
  );
}

function FlagItem({ flag: f }: { flag: HealthFlag }) {
  return (
    <li className="rounded-md bg-neutral-50 p-2.5">
      <div className="flex items-center gap-2">
        <span
          className={cn(
            "rounded border px-1.5 py-0.5 text-[10px] font-medium uppercase",
            SEVERITY_STYLE[f.severity],
          )}
        >
          {f.severity}
        </span>
        <span className="text-sm font-medium text-neutral-800">{f.description}</span>
      </div>
      {f.remediation && (
        <p className="mt-1 text-xs text-neutral-600">
          <span className="font-medium">Remediation: </span>
          {f.remediation}
        </p>
      )}
      {f.references.length > 0 && (
        <div className="mt-1 flex flex-wrap gap-1.5">
          {f.references.map((r) => (
            <Link
              key={r.id}
              href={`/modules/asset-library/${r.id}`}
              className="rounded bg-white px-1.5 py-0.5 text-[11px] text-indigo-600 hover:underline"
            >
              {r.title || r.id}
            </Link>
          ))}
        </div>
      )}
    </li>
  );
}

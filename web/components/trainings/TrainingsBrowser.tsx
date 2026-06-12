"use client";

import { useEffect, useMemo, useState, useSyncExternalStore } from "react";
import Link from "next/link";
import { BookmarkCheck, BookmarkPlus, Clock, ExternalLink } from "lucide-react";

import { getDisplayName } from "@/lib/auth";
import {
  formatDuration,
  LEVELS,
  SOURCES,
  THEMES,
  type TrainingSummary,
} from "@/lib/trainings";
import { cn } from "@/lib/utils";

import { listTrainings, saveTraining } from "@/app/(authenticated)/modules/trainings/actions";

type Tab = "tutorial" | "hosted";

export function TrainingsBrowser() {
  const name = useSyncExternalStore(
    () => () => {},
    () => getDisplayName(),
    () => null,
  );

  const [tab, setTab] = useState<Tab>("tutorial");
  const [theme, setTheme] = useState("");
  const [source, setSource] = useState("");
  const [level, setLevel] = useState("");
  const [items, setItems] = useState<TrainingSummary[]>([]);
  const [loaded, setLoaded] = useState(false);
  const [savingId, setSavingId] = useState<string | null>(null);

  useEffect(() => {
    listTrainings({ theme, source, level }, name ?? undefined)
      .then((r) => setItems(r.trainings ?? []))
      .finally(() => setLoaded(true));
  }, [theme, source, level, name]);

  const hosted = useMemo(() => items.filter((t) => t.kind === "hosted"), [items]);
  const tutorials = useMemo(() => items.filter((t) => t.kind === "tutorial"), [items]);

  // Tutorials grouped by theme (preserve THEMES order, then any extras).
  const grouped = useMemo(() => {
    const by: Record<string, TrainingSummary[]> = {};
    for (const t of tutorials) (by[t.theme] ??= []).push(t);
    const ordered = [...THEMES.filter((th) => by[th]), ...Object.keys(by).filter((k) => !THEMES.includes(k))];
    return ordered.map((th) => [th, by[th]] as const);
  }, [tutorials]);

  async function onToggle(t: TrainingSummary) {
    if (!name) return;
    setSavingId(t.id);
    try {
      const res = await saveTraining(name, t.id, !!t.saved);
      if (res.status === "ok") {
        setItems((prev) => prev.map((x) => (x.id === t.id ? { ...x, saved: res.saved } : x)));
      }
    } finally {
      setSavingId(null);
    }
  }

  const active = tab === "hosted" ? hosted : tutorials;

  return (
    <div className="flex flex-col gap-8 lg:flex-row">
      {/* Filter rail */}
      <aside className="w-full shrink-0 space-y-4 lg:w-56">
        <Select label="Theme" value={theme} onChange={setTheme} options={THEMES} />
        <Select label="Source" value={source} onChange={setSource} options={SOURCES} />
        <Select label="Level" value={level} onChange={setLevel} options={LEVELS} capitalize />
      </aside>

      {/* Main */}
      <div className="min-w-0 flex-1">
        {/* Tabs */}
        <div className="mb-5 flex gap-1 border-b border-slate-200">
          <TabButton active={tab === "tutorial"} onClick={() => setTab("tutorial")}>
            Recommended Tutorials ({tutorials.length})
          </TabButton>
          <TabButton active={tab === "hosted"} onClick={() => setTab("hosted")}>
            Hosted ({hosted.length})
          </TabButton>
        </div>

        {!loaded ? (
          <div className="grid gap-4 sm:grid-cols-2">
            {[0, 1, 2, 3].map((i) => (
              <div key={i} className="h-40 animate-pulse rounded-lg bg-slate-100" />
            ))}
          </div>
        ) : active.length === 0 ? (
          <p className="text-sm text-slate-400">No trainings match these filters.</p>
        ) : tab === "hosted" ? (
          <div className="grid gap-4 sm:grid-cols-2">
            {hosted.map((t) => (
              <TrainingCard key={t.id} t={t} name={name} saving={savingId === t.id} onToggle={onToggle} />
            ))}
          </div>
        ) : (
          <div className="space-y-8">
            {grouped.map(([th, list]) => (
              <section key={th}>
                <h2 className="mb-3 text-sm font-semibold uppercase tracking-wide text-slate-500">
                  {th}
                </h2>
                <div className="grid gap-4 sm:grid-cols-2">
                  {list.map((t) => (
                    <TrainingCard
                      key={t.id}
                      t={t}
                      name={name}
                      saving={savingId === t.id}
                      onToggle={onToggle}
                    />
                  ))}
                </div>
              </section>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

function TrainingCard({
  t,
  name,
  saving,
  onToggle,
}: {
  t: TrainingSummary;
  name: string | null;
  saving: boolean;
  onToggle: (t: TrainingSummary) => void;
}) {
  return (
    <div className="flex flex-col rounded-lg border border-slate-200 p-4 transition hover:border-indigo-300">
      <div className="mb-2 flex items-start justify-between gap-2">
        <SourceBadge source={t.source} />
        <button
          onClick={() => onToggle(t)}
          disabled={!name || saving}
          title={name ? (t.saved ? "Saved — click to remove" : "Save to dashboard") : "Set a display name to save"}
          className={cn(
            "shrink-0 rounded p-1 transition disabled:opacity-40",
            t.saved ? "text-green-600" : "text-slate-400 hover:text-indigo-600",
          )}
        >
          {t.saved ? <BookmarkCheck className="h-4 w-4" /> : <BookmarkPlus className="h-4 w-4" />}
        </button>
      </div>
      <Link href={`/modules/trainings/${t.id}`} className="group">
        <h3 className="text-sm font-semibold text-slate-900 group-hover:text-indigo-700">{t.title}</h3>
      </Link>
      <p className="mt-1 line-clamp-2 text-xs text-slate-500">{t.summary}</p>
      <div className="mt-3 flex flex-wrap items-center gap-2 text-[11px] text-slate-500">
        <span className="rounded bg-indigo-50 px-1.5 py-0.5 font-medium text-indigo-700">{t.theme}</span>
        <span className="capitalize">{t.level}</span>
        {t.duration_min > 0 && (
          <span className="flex items-center gap-1">
            <Clock className="h-3 w-3" /> {formatDuration(t.duration_min)}
          </span>
        )}
      </div>
      <a
        href={t.url}
        target="_blank"
        rel="noopener noreferrer"
        className="mt-3 inline-flex items-center gap-1 text-xs font-medium text-indigo-600 hover:text-indigo-800"
      >
        {t.kind === "hosted" ? "Watch recording" : "Open course"}
        <ExternalLink className="h-3 w-3" />
      </a>
    </div>
  );
}

function SourceBadge({ source }: { source: string }) {
  const internal = source.toLowerCase() === "internal";
  return (
    <span
      className={cn(
        "rounded px-1.5 py-0.5 text-[11px] font-medium",
        internal ? "bg-amber-100 text-amber-800" : "bg-slate-100 text-slate-600",
      )}
    >
      {source}
    </span>
  );
}

function Select({
  label,
  value,
  onChange,
  options,
  capitalize,
}: {
  label: string;
  value: string;
  onChange: (v: string) => void;
  options: string[];
  capitalize?: boolean;
}) {
  return (
    <div>
      <label className="mb-1 block text-xs font-semibold uppercase tracking-wide text-slate-500">
        {label}
      </label>
      <select
        value={value}
        onChange={(e) => onChange(e.target.value)}
        className={cn(
          "w-full rounded-md border border-slate-200 px-2 py-1.5 text-sm text-slate-700 focus:border-indigo-400 focus:outline-none",
          capitalize && "capitalize",
        )}
      >
        <option value="">All</option>
        {options.map((o) => (
          <option key={o} value={o}>
            {o}
          </option>
        ))}
      </select>
    </div>
  );
}

function TabButton({
  active,
  onClick,
  children,
}: {
  active: boolean;
  onClick: () => void;
  children: React.ReactNode;
}) {
  return (
    <button
      onClick={onClick}
      className={cn(
        "-mb-px border-b-2 px-3 py-2 text-sm font-medium transition",
        active
          ? "border-indigo-600 text-indigo-700"
          : "border-transparent text-slate-500 hover:text-slate-800",
      )}
    >
      {children}
    </button>
  );
}

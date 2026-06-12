"use client";

import { useEffect, useMemo, useState, useSyncExternalStore } from "react";
import Link from "next/link";
import {
  BookOpen,
  CheckCircle2,
  Circle,
  Compass,
  GraduationCap,
  Library,
  Loader2,
  Users,
  Wrench,
} from "lucide-react";

import { GuidedTour, startTour, type TourStep } from "@/components/GuidedTour";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { getDisplayName } from "@/lib/auth";
import {
  type ActionItem,
  humanizeIndustry,
  type OnboardingPath,
} from "@/lib/onboarding";

import { generateOnboardingPath, updateChecklistItem } from "../actions";

const TOUR_STEPS: TourStep[] = [
  {
    title: "Welcome to the AI CoE platform",
    body: "This is your personalized onboarding path. It pulls from the same knowledge vault every module uses — tailored to the role and focus you just told us.",
  },
  {
    title: "Your starting points",
    body: "Top assets, learning paths, key tools, and people to know are picked for your industry focus and AI background. Each card links straight into the relevant module.",
  },
  {
    title: "Your 30-day checklist",
    body: "Work through the checklist at your own pace. Tick items off — your progress is saved to your profile and follows you across sessions.",
  },
];

const WEEK_LABELS: Record<number, string> = {
  1: "Week 1",
  2: "Week 2",
  3: "Week 3",
  4: "Week 4",
};

export default function OnboardingPathPage() {
  const name = useSyncExternalStore(
    () => () => {},
    () => getDisplayName(),
    () => null,
  );
  const [path, setPath] = useState<OnboardingPath | null>(null);
  const [loaded, setLoaded] = useState(false);
  const [checklist, setChecklist] = useState<ActionItem[]>([]);
  const [busyId, setBusyId] = useState<string | null>(null);

  // (The `!name` case is handled in render, so no setState is needed here.)
  useEffect(() => {
    if (!name) return;
    let active = true;
    generateOnboardingPath(name)
      .then((p) => {
        if (!active) return;
        setPath(p);
        setChecklist(p.first_actions ?? []);
      })
      .finally(() => active && setLoaded(true));
    return () => {
      active = false;
    };
  }, [name]);

  const progress = useMemo(() => {
    const total = checklist.length;
    const done = checklist.filter((a) => a.done).length;
    return { total, done, pct: total ? Math.round((done / total) * 100) : 0 };
  }, [checklist]);

  const byWeek = useMemo(() => {
    const groups = new Map<number, ActionItem[]>();
    for (const a of checklist) {
      const list = groups.get(a.week) ?? [];
      list.push(a);
      groups.set(a.week, list);
    }
    return [...groups.entries()].sort((a, b) => a[0] - b[0]);
  }, [checklist]);

  async function toggle(item: ActionItem) {
    if (!name) return;
    const next = !item.done;
    setBusyId(item.id);
    // Optimistic.
    setChecklist((prev) => prev.map((a) => (a.id === item.id ? { ...a, done: next } : a)));
    try {
      const res = await updateChecklistItem(name, item.id, next);
      if (res.status !== "ok") {
        setChecklist((prev) => prev.map((a) => (a.id === item.id ? { ...a, done: item.done } : a)));
      }
    } catch {
      setChecklist((prev) => prev.map((a) => (a.id === item.id ? { ...a, done: item.done } : a)));
    } finally {
      setBusyId(null);
    }
  }

  if (!name) {
    return (
      <div className="mx-auto max-w-2xl">
        <h1 className="text-2xl font-semibold">Your onboarding path</h1>
        <p className="mt-2 text-sm text-neutral-500">
          Set a display name (log out and back in) to build your path.
        </p>
      </div>
    );
  }

  if (loaded && (!path || path.status !== "ok")) {
    return (
      <div className="mx-auto max-w-2xl">
        <h1 className="text-2xl font-semibold">Your onboarding path</h1>
        <p className="mt-3 text-sm text-neutral-500">
          We couldn&apos;t build your path yet.{" "}
          <Link href="/modules/onboarding/profile" className="text-indigo-600 hover:underline">
            Complete your profile
          </Link>{" "}
          to get started.
        </p>
      </div>
    );
  }

  const profile = path?.profile;

  return (
    <div className="mx-auto max-w-5xl">
      <GuidedTour tourId="onboarding-path" steps={TOUR_STEPS} />

      <div className="mb-6 flex flex-wrap items-start justify-between gap-3">
        <div>
          <h1 className="flex items-center gap-2 text-2xl font-semibold">
            <GraduationCap className="h-6 w-6 text-indigo-600" />
            Your onboarding path
          </h1>
          {profile && (
            <p className="mt-1 text-sm text-slate-500">
              Tailored for a{" "}
              <span className="font-medium text-slate-700">
                {profile.role.replace(/-/g, " ")}
              </span>
              {profile.industry_focus.length > 0 && (
                <> focused on {profile.industry_focus.map(humanizeIndustry).join(", ")}</>
              )}
              {" · "}
              {profile.ai_background} AI background
            </p>
          )}
        </div>
        <div className="flex gap-2">
          <Button variant="outline" size="sm" onClick={() => startTour("onboarding-path")}>
            <Compass className="h-4 w-4" /> Take a tour
          </Button>
          <Link href="/modules/onboarding/profile">
            <Button variant="ghost" size="sm">
              Edit profile
            </Button>
          </Link>
        </div>
      </div>

      {!loaded ? (
        <div className="grid gap-4 lg:grid-cols-2">
          {Array.from({ length: 4 }).map((_, i) => (
            <div key={i} className="h-48 animate-pulse rounded-xl bg-neutral-100" />
          ))}
        </div>
      ) : (
        <>
          <div className="grid gap-5 lg:grid-cols-2">
            {/* Top assets */}
            <Section icon={Library} title="Top assets to know" href="/modules/asset-library">
              {(path?.top_assets ?? []).length === 0 ? (
                <Empty>No matching assets yet.</Empty>
              ) : (
                <ul className="space-y-2">
                  {path!.top_assets.map((a) => (
                    <li key={a.id}>
                      <Link
                        href={`/modules/asset-library/${a.id}`}
                        className="block rounded-md border border-neutral-200 px-3 py-2 text-sm transition hover:border-indigo-300 hover:bg-indigo-50/40"
                      >
                        <span className="font-medium text-neutral-800">{a.title || a.id}</span>
                        <span className="mt-0.5 block text-xs text-neutral-500">
                          {humanizeIndustry(a.industry)} · stage {a.ai_stage}
                        </span>
                      </Link>
                    </li>
                  ))}
                </ul>
              )}
            </Section>

            {/* Learning paths */}
            <Section
              icon={BookOpen}
              title="Recommended learning"
              href="/modules/community/learning"
            >
              {(path?.learning_paths ?? []).length === 0 ? (
                <Empty>No learning paths matched your role.</Empty>
              ) : (
                <ul className="space-y-2">
                  {path!.learning_paths.map((lp) => (
                    <li
                      key={lp.id}
                      className="rounded-md border border-neutral-200 px-3 py-2 text-sm"
                    >
                      <span className="font-medium text-neutral-800">{lp.title}</span>
                      <span className="mt-0.5 block text-xs text-neutral-500">
                        {lp.role.replace(/-/g, " ")}
                        {lp.duration ? ` · ${lp.duration}` : ""}
                      </span>
                    </li>
                  ))}
                </ul>
              )}
            </Section>

            {/* Key tools */}
            <Section icon={Wrench} title="Key tools for your role" href="/modules/tools-repo">
              {(path?.key_tools ?? []).length === 0 ? (
                <Empty>No tools to suggest yet.</Empty>
              ) : (
                <ul className="space-y-2">
                  {path!.key_tools.map((t) => (
                    <li key={t.id}>
                      <Link
                        href={`/modules/tools-repo/${t.id}`}
                        className="block rounded-md border border-neutral-200 px-3 py-2 text-sm transition hover:border-indigo-300 hover:bg-indigo-50/40"
                      >
                        <span className="font-medium text-neutral-800">{t.name || t.id}</span>
                        <span className="mt-0.5 block text-xs text-neutral-500">{t.category}</span>
                      </Link>
                    </li>
                  ))}
                </ul>
              )}
            </Section>

            {/* Suggested connections */}
            <Section icon={Users} title="People to know" href="/modules/community/experts">
              {(path?.suggested_connections ?? []).length === 0 ? (
                <Empty>No experts matched your focus.</Empty>
              ) : (
                <ul className="space-y-2">
                  {path!.suggested_connections.map((e) => (
                    <li
                      key={e.id}
                      className="rounded-md border border-neutral-200 px-3 py-2 text-sm"
                    >
                      <span className="font-medium text-neutral-800">{e.name}</span>
                      <span className="mt-0.5 block text-xs text-neutral-500">
                        {e.title}
                        {e.expertise.length > 0 ? ` · ${e.expertise.slice(0, 2).join(", ")}` : ""}
                      </span>
                    </li>
                  ))}
                </ul>
              )}
            </Section>
          </div>

          {/* 30-day checklist */}
          <div className="mt-8">
            <div className="mb-3 flex flex-wrap items-center justify-between gap-2">
              <h2 className="text-lg font-semibold text-neutral-900">Your first 30 days</h2>
              <span className="text-sm text-neutral-500">
                {progress.done} of {progress.total} done
              </span>
            </div>
            <div className="mb-5 h-2 w-full overflow-hidden rounded-full bg-neutral-200">
              <div
                className="h-full rounded-full bg-indigo-600 transition-all"
                style={{ width: `${progress.pct}%` }}
              />
            </div>

            <div className="space-y-6">
              {byWeek.map(([week, items]) => (
                <div key={week}>
                  <h3 className="mb-2 text-xs font-semibold uppercase tracking-wide text-neutral-400">
                    {WEEK_LABELS[week] ?? `Week ${week}`}
                  </h3>
                  <div className="space-y-2">
                    {items.map((item) => (
                      <button
                        key={item.id}
                        onClick={() => toggle(item)}
                        disabled={busyId === item.id}
                        className={`flex w-full items-start gap-3 rounded-lg border px-4 py-3 text-left transition ${
                          item.done
                            ? "border-green-200 bg-green-50/60"
                            : "border-neutral-200 hover:bg-neutral-50"
                        }`}
                      >
                        <span className="mt-0.5 shrink-0">
                          {busyId === item.id ? (
                            <Loader2 className="h-5 w-5 animate-spin text-neutral-400" />
                          ) : item.done ? (
                            <CheckCircle2 className="h-5 w-5 text-green-600" />
                          ) : (
                            <Circle className="h-5 w-5 text-neutral-300" />
                          )}
                        </span>
                        <span className="min-w-0">
                          <span
                            className={`block text-sm font-medium ${
                              item.done ? "text-neutral-500 line-through" : "text-neutral-800"
                            }`}
                          >
                            {item.title}
                          </span>
                          <span className="mt-0.5 block text-xs text-neutral-500">
                            {item.description}
                          </span>
                          {item.module_route && (
                            <Link
                              href={item.module_route}
                              onClick={(e) => e.stopPropagation()}
                              className="mt-1 inline-block text-xs font-medium text-indigo-600 hover:underline"
                            >
                              Open module →
                            </Link>
                          )}
                        </span>
                      </button>
                    ))}
                  </div>
                </div>
              ))}
            </div>
          </div>
        </>
      )}
    </div>
  );
}

function Section({
  icon: Icon,
  title,
  href,
  children,
}: {
  icon: typeof Library;
  title: string;
  href: string;
  children: React.ReactNode;
}) {
  return (
    <Card className="h-full">
      <CardContent className="pt-6">
        <div className="mb-3 flex items-center justify-between">
          <h2 className="flex items-center gap-2 text-base font-semibold text-neutral-900">
            <Icon className="h-5 w-5 text-indigo-600" />
            {title}
          </h2>
          <Link href={href} className="text-xs font-medium text-indigo-600 hover:underline">
            View all
          </Link>
        </div>
        {children}
      </CardContent>
    </Card>
  );
}

function Empty({ children }: { children: React.ReactNode }) {
  return <p className="text-sm text-neutral-400">{children}</p>;
}

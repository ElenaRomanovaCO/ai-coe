"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { Clock, GraduationCap } from "lucide-react";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { humanizeRole, LEARNING_ROLES, type LearningPath } from "@/lib/community";
import { cn } from "@/lib/utils";

import { listLearningPaths } from "../actions";

const STAGES = [0, 1, 2, 3, 4, 5];

export default function LearningPathsPage() {
  const [role, setRole] = useState<string>("");
  const [stage, setStage] = useState<number | null>(null);
  const [paths, setPaths] = useState<LearningPath[]>([]);
  const [loaded, setLoaded] = useState(false);

  useEffect(() => {
    listLearningPaths(role || undefined, stage ?? undefined)
      .then((r) => setPaths(r.learning_paths ?? []))
      .finally(() => setLoaded(true));
  }, [role, stage]);

  return (
    <div className="mx-auto max-w-5xl">
      <nav className="mb-4 text-sm text-slate-500">
        <Link href="/modules/community" className="hover:text-slate-900">
          Community Hub
        </Link>
        <span className="mx-2">/</span>
        <span className="text-slate-700">Learning Paths</span>
      </nav>

      <h1 className="mb-1 flex items-center gap-2 text-2xl font-semibold">
        <GraduationCap className="h-6 w-6 text-indigo-600" />
        Learning Paths
      </h1>
      <p className="mb-5 text-sm text-slate-500">
        Curated paths by role and maturity stage. Filter to your situation.
      </p>

      <div className="flex flex-col gap-8 lg:flex-row">
        {/* Filters */}
        <aside className="w-full shrink-0 space-y-5 lg:w-56">
          <div>
            <h2 className="mb-2 text-xs font-semibold uppercase tracking-wide text-slate-500">Role</h2>
            <div className="flex flex-wrap gap-1.5">
              <FilterChip active={role === ""} onClick={() => setRole("")}>
                All
              </FilterChip>
              {LEARNING_ROLES.map((r) => (
                <FilterChip key={r} active={role === r} onClick={() => setRole(r)}>
                  {humanizeRole(r)}
                </FilterChip>
              ))}
            </div>
          </div>
          <div>
            <h2 className="mb-2 text-xs font-semibold uppercase tracking-wide text-slate-500">
              Stage
            </h2>
            <div className="flex flex-wrap gap-1.5">
              <FilterChip active={stage === null} onClick={() => setStage(null)}>
                Any
              </FilterChip>
              {STAGES.map((s) => (
                <FilterChip key={s} active={stage === s} onClick={() => setStage(s)}>
                  {s}
                </FilterChip>
              ))}
            </div>
          </div>
        </aside>

        {/* List */}
        <div className="min-w-0 flex-1">
          {!loaded ? (
            <div className="space-y-3">
              {[0, 1, 2].map((i) => (
                <div key={i} className="h-28 animate-pulse rounded-lg bg-slate-100" />
              ))}
            </div>
          ) : paths.length === 0 ? (
            <p className="text-sm text-slate-400">No learning paths match these filters.</p>
          ) : (
            <div className="space-y-4">
              {paths.map((p) => (
                <Card key={p.id}>
                  <CardHeader>
                    <CardTitle className="text-base">{p.title}</CardTitle>
                  </CardHeader>
                  <CardContent className="space-y-3">
                    <div className="flex flex-wrap items-center gap-2 text-xs text-slate-500">
                      <span className="rounded bg-indigo-50 px-2 py-0.5 font-medium text-indigo-700">
                        {humanizeRole(p.role)}
                      </span>
                      {p.stage !== null && (
                        <span className="rounded bg-slate-100 px-2 py-0.5">Stage {p.stage}</span>
                      )}
                      {p.duration && (
                        <span className="flex items-center gap-1">
                          <Clock className="h-3 w-3" /> {p.duration}
                        </span>
                      )}
                    </div>
                    {p.modules.length > 0 && (
                      <ul className="list-disc space-y-0.5 pl-5 text-sm text-slate-700">
                        {p.modules.map((m, i) => (
                          <li key={i}>{m}</li>
                        ))}
                      </ul>
                    )}
                  </CardContent>
                </Card>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

function FilterChip({
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
        "rounded-full border px-2.5 py-1 text-xs transition",
        active
          ? "border-indigo-600 bg-indigo-600 text-white"
          : "border-slate-200 text-slate-600 hover:border-slate-300",
      )}
    >
      {children}
    </button>
  );
}

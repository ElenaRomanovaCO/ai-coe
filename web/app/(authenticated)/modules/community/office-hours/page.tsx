"use client";

import { useEffect, useState, useSyncExternalStore } from "react";
import Link from "next/link";
import { CalendarDays, Check, Loader2 } from "lucide-react";

import { Card, CardContent } from "@/components/ui/card";
import { getDisplayName } from "@/lib/auth";
import type { OfficeHour } from "@/lib/community";

import { listOfficeHours, signupOfficeHours } from "../actions";

function formatDate(iso: string): string {
  if (!iso) return "";
  const d = new Date(iso);
  if (isNaN(d.getTime())) return iso;
  return d.toLocaleString(undefined, {
    weekday: "short",
    month: "short",
    day: "numeric",
    hour: "numeric",
    minute: "2-digit",
  });
}

export default function OfficeHoursPage() {
  const name = useSyncExternalStore(
    () => () => {},
    () => getDisplayName(),
    () => null,
  );
  const [sessions, setSessions] = useState<OfficeHour[]>([]);
  const [loaded, setLoaded] = useState(false);
  const [busyId, setBusyId] = useState<string | null>(null);

  useEffect(() => {
    listOfficeHours(name ?? undefined)
      .then((r) => setSessions(r.office_hours ?? []))
      .finally(() => setLoaded(true));
  }, [name]);

  async function onToggle(oh: OfficeHour) {
    if (!name) return;
    setBusyId(oh.id);
    try {
      const res = await signupOfficeHours(name, oh.id, oh.signed_up);
      if (res.status === "ok") {
        setSessions((prev) =>
          prev.map((s) => (s.id === oh.id ? { ...s, signed_up: res.signed_up } : s)),
        );
      }
    } finally {
      setBusyId(null);
    }
  }

  return (
    <div className="mx-auto max-w-4xl">
      <nav className="mb-4 text-sm text-slate-500">
        <Link href="/modules/community" className="hover:text-slate-900">
          Community Hub
        </Link>
        <span className="mx-2">/</span>
        <span className="text-slate-700">Office Hours</span>
      </nav>

      <h1 className="mb-1 flex items-center gap-2 text-2xl font-semibold">
        <CalendarDays className="h-6 w-6 text-indigo-600" />
        Office Hours
      </h1>
      <p className="mb-5 text-sm text-slate-500">
        {name
          ? "Drop-in clinics with the guild. Sign up for the sessions you want to join."
          : "Set a display name (log out and back in) to sign up for sessions."}
      </p>

      {!loaded ? (
        <div className="space-y-3">
          {[0, 1, 2].map((i) => (
            <div key={i} className="h-24 animate-pulse rounded-lg bg-slate-100" />
          ))}
        </div>
      ) : sessions.length === 0 ? (
        <p className="text-sm text-slate-400">No upcoming office hours.</p>
      ) : (
        <div className="space-y-4">
          {sessions.map((oh) => (
            <Card key={oh.id}>
              <CardContent className="flex items-start justify-between gap-4 pt-6">
                <div className="min-w-0">
                  <h3 className="text-base font-semibold text-slate-900">{oh.title}</h3>
                  <div className="mt-1 flex flex-wrap items-center gap-x-3 gap-y-1 text-xs text-slate-500">
                    <span>{formatDate(oh.date)}</span>
                    {oh.host && <span>· {oh.host}</span>}
                    {oh.capacity !== null && <span>· {oh.capacity} seats</span>}
                  </div>
                  {oh.topic && <p className="mt-2 text-sm text-slate-600">{oh.topic}</p>}
                </div>
                <button
                  onClick={() => onToggle(oh)}
                  disabled={!name || busyId === oh.id}
                  className={
                    oh.signed_up
                      ? "flex shrink-0 items-center gap-1 rounded-md border border-green-300 bg-green-50 px-3 py-1.5 text-sm font-medium text-green-700 disabled:opacity-50"
                      : "flex shrink-0 items-center gap-1 rounded-md bg-indigo-600 px-3 py-1.5 text-sm font-medium text-white hover:bg-indigo-700 disabled:opacity-50"
                  }
                >
                  {busyId === oh.id ? (
                    <Loader2 className="h-4 w-4 animate-spin" />
                  ) : oh.signed_up ? (
                    <Check className="h-4 w-4" />
                  ) : null}
                  {oh.signed_up ? "Signed up" : "Sign up"}
                </button>
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}

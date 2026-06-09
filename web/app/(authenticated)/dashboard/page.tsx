"use client";

import { useEffect, useState, useSyncExternalStore } from "react";

import { ActiveEngagementsCard } from "@/components/dashboard/ActiveEngagementsCard";
import { LearningProgressCard } from "@/components/dashboard/LearningProgressCard";
import { QuickActionsCard } from "@/components/dashboard/QuickActionsCard";
import { RecentChatsCard } from "@/components/dashboard/RecentChatsCard";
import { RecommendationsCard } from "@/components/dashboard/RecommendationsCard";
import { SavedAssetsCard } from "@/components/dashboard/SavedAssetsCard";
import { Button } from "@/components/ui/button";
import { getDisplayName } from "@/lib/auth";
import { OPEN_CHAT_EVENT, type DashboardSummary } from "@/lib/dashboard";

import { getDashboardSummary } from "./actions";

// Client-driven: the dashboard is personalized by display_name, which lives in
// localStorage (our auth model), so it can't be fetched in a Server Component.
export default function DashboardPage() {
  const name = useSyncExternalStore(
    () => () => {},
    () => getDisplayName(),
    () => null,
  );
  const [summary, setSummary] = useState<DashboardSummary | null>(null);
  const [loaded, setLoaded] = useState(false);

  // setState only runs in the async callbacks (not synchronously in the effect
  // body); the no-name case is handled in render, not via setState.
  useEffect(() => {
    if (!name) return;
    let active = true;
    getDashboardSummary(name)
      .then((s) => {
        if (active) {
          setSummary(s);
          setLoaded(true);
        }
      })
      .catch(() => active && setLoaded(true));
    return () => {
      active = false;
    };
  }, [name]);

  function openChat() {
    window.dispatchEvent(new CustomEvent(OPEN_CHAT_EVENT));
  }

  if (!name) {
    return (
      <div className="mx-auto max-w-3xl">
        <h1 className="text-2xl font-semibold">Dashboard</h1>
        <p className="mt-2 text-sm text-neutral-500">
          Set a display name (log out and back in) to see your personalized dashboard.
        </p>
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-6xl">
      <div className="mb-6 flex flex-wrap items-center justify-between gap-3">
        <h1 className="text-2xl font-semibold">Hi, {name}</h1>
        <Button onClick={openChat} disabled={!summary?.last_session_id}>
          Resume Last Chat
        </Button>
      </div>

      {!loaded ? (
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {Array.from({ length: 6 }).map((_, i) => (
            <div key={i} className="h-40 animate-pulse rounded-xl bg-neutral-100" />
          ))}
        </div>
      ) : (
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
          <SavedAssetsCard assets={summary?.saved_assets ?? []} />
          <RecentChatsCard chats={summary?.recent_chats ?? []} onResume={openChat} />
          <RecommendationsCard assets={summary?.recommendations ?? []} />
          <QuickActionsCard />
          <ActiveEngagementsCard />
          <LearningProgressCard />
        </div>
      )}
    </div>
  );
}

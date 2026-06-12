"use client";

import { useEffect, useState, useSyncExternalStore } from "react";
import { useRouter } from "next/navigation";

import { ActiveEngagementsCard } from "@/components/dashboard/ActiveEngagementsCard";
import { LearningProgressCard } from "@/components/dashboard/LearningProgressCard";
import { QuickActionsCard } from "@/components/dashboard/QuickActionsCard";
import { RecentChatsCard } from "@/components/dashboard/RecentChatsCard";
import { RecommendationsCard } from "@/components/dashboard/RecommendationsCard";
import { SavedAssetsCard } from "@/components/dashboard/SavedAssetsCard";
import { SavedTrainingsCard } from "@/components/dashboard/SavedTrainingsCard";
import { Button } from "@/components/ui/button";
import { getDisplayName } from "@/lib/auth";
import { OPEN_CHAT_EVENT, type DashboardSummary } from "@/lib/dashboard";

import { getOnboardingProfile } from "../modules/onboarding/actions";
import { getDashboardSummary } from "./actions";

const ONBOARDING_PROMPTED_KEY = "onboarding_prompted";

// Client-driven: the dashboard is personalized by display_name, which lives in
// localStorage (our auth model), so it can't be fetched in a Server Component.
export default function DashboardPage() {
  const router = useRouter();
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

  // First-time hook (FR-068/Task-24 step 4): the first time a user lands on the
  // dashboard, if they haven't completed onboarding, send them to the profile
  // capture. Guarded by a one-shot localStorage flag so it never hijacks return
  // visits or other navigation.
  useEffect(() => {
    if (!name) return;
    let prompted = "1";
    try {
      prompted = window.localStorage.getItem(ONBOARDING_PROMPTED_KEY) ?? "";
    } catch {
      prompted = "1";
    }
    if (prompted) return;
    let active = true;
    getOnboardingProfile(name)
      .then((r) => {
        if (!active) return;
        try {
          window.localStorage.setItem(ONBOARDING_PROMPTED_KEY, "1");
        } catch {
          // best-effort; redirect still happens once below
        }
        if (!r.onboarding_completed) router.push("/modules/onboarding/profile");
      })
      .catch(() => {});
    return () => {
      active = false;
    };
  }, [name, router]);

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
          <SavedTrainingsCard name={name} />
          <ActiveEngagementsCard />
          <LearningProgressCard />
        </div>
      )}
    </div>
  );
}

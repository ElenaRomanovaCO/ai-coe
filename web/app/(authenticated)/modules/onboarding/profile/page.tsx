"use client";

import { useEffect, useState, useSyncExternalStore } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { GraduationCap, Loader2 } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { getDisplayName } from "@/lib/auth";
import {
  type AiBackground,
  BACKGROUND_OPTIONS,
  humanizeIndustry,
  INDUSTRY_OPTIONS,
  type OnboardingProfile,
  type OnboardingRole,
  ROLE_OPTIONS,
} from "@/lib/onboarding";

import { getOnboardingProfile, saveOnboardingProfile } from "../actions";

export default function OnboardingProfilePage() {
  const router = useRouter();
  const name = useSyncExternalStore(
    () => () => {},
    () => getDisplayName(),
    () => null,
  );

  const [role, setRole] = useState<OnboardingRole>("consultant");
  const [years, setYears] = useState<string>("0");
  const [background, setBackground] = useState<AiBackground>("novice");
  const [industries, setIndustries] = useState<string[]>([]);
  const [goals, setGoals] = useState<string>("");
  const [saving, setSaving] = useState(false);
  const [loaded, setLoaded] = useState(false);

  // Prefill from any saved profile so the form doubles as "edit my profile".
  // (The `!name` case is handled in render, so no setState is needed here.)
  useEffect(() => {
    if (!name) return;
    let active = true;
    getOnboardingProfile(name)
      .then((r) => {
        if (active && r.onboarding) {
          setRole(r.onboarding.role);
          setYears(String(r.onboarding.experience_years ?? 0));
          setBackground(r.onboarding.ai_background);
          setIndustries(r.onboarding.industry_focus ?? []);
          setGoals((r.onboarding.goals ?? []).join("\n"));
        }
      })
      .finally(() => active && setLoaded(true));
    return () => {
      active = false;
    };
  }, [name]);

  function toggleIndustry(ind: string) {
    setIndustries((prev) =>
      prev.includes(ind) ? prev.filter((x) => x !== ind) : [...prev, ind],
    );
  }

  async function onSubmit() {
    if (!name) return;
    setSaving(true);
    const profile: OnboardingProfile = {
      role,
      experience_years: Number.parseInt(years, 10) || 0,
      industry_focus: industries,
      ai_background: background,
      goals: goals
        .split("\n")
        .map((g) => g.trim())
        .filter(Boolean),
    };
    try {
      const res = await saveOnboardingProfile(name, profile);
      if (res.status === "ok") router.push("/modules/onboarding/path");
    } finally {
      setSaving(false);
    }
  }

  if (!name) {
    return (
      <div className="mx-auto max-w-2xl">
        <h1 className="text-2xl font-semibold">Onboarding</h1>
        <p className="mt-2 text-sm text-neutral-500">
          Set a display name (log out and back in) to build your onboarding path.
        </p>
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-2xl">
      <nav className="mb-4 text-sm text-slate-500">
        <Link href="/modules/onboarding" className="hover:text-slate-900">
          Onboarding
        </Link>
        <span className="mx-2">/</span>
        <span className="text-slate-700">Your Profile</span>
      </nav>

      <h1 className="mb-1 flex items-center gap-2 text-2xl font-semibold">
        <GraduationCap className="h-6 w-6 text-indigo-600" />
        Tell us about you
      </h1>
      <p className="mb-6 text-sm text-slate-500">
        We&apos;ll tailor your first-30-days path — top assets, learning, tools, and people — to
        your role and focus.
      </p>

      {!loaded ? (
        <div className="h-96 animate-pulse rounded-xl bg-neutral-100" />
      ) : (
        <Card>
          <CardContent className="space-y-6 pt-6">
            {/* Role */}
            <div>
              <label className="mb-1.5 block text-sm font-medium text-neutral-800">Your role</label>
              <div className="grid gap-2 sm:grid-cols-2">
                {ROLE_OPTIONS.map((o) => (
                  <button
                    key={o.value}
                    type="button"
                    onClick={() => setRole(o.value)}
                    className={`rounded-md border px-3 py-2 text-left text-sm transition ${
                      role === o.value
                        ? "border-indigo-500 bg-indigo-50 text-indigo-700"
                        : "border-neutral-300 hover:bg-neutral-50"
                    }`}
                  >
                    {o.label}
                  </button>
                ))}
              </div>
            </div>

            {/* Experience */}
            <div>
              <label className="mb-1.5 block text-sm font-medium text-neutral-800">
                Years of experience
              </label>
              <Input
                type="number"
                min={0}
                max={50}
                value={years}
                onChange={(e) => setYears(e.target.value)}
                className="max-w-[8rem]"
              />
            </div>

            {/* AI background */}
            <div>
              <label className="mb-1.5 block text-sm font-medium text-neutral-800">
                AI delivery background
              </label>
              <div className="grid gap-2 sm:grid-cols-3">
                {BACKGROUND_OPTIONS.map((o) => (
                  <button
                    key={o.value}
                    type="button"
                    onClick={() => setBackground(o.value)}
                    className={`rounded-md border px-3 py-2 text-left text-sm transition ${
                      background === o.value
                        ? "border-indigo-500 bg-indigo-50 text-indigo-700"
                        : "border-neutral-300 hover:bg-neutral-50"
                    }`}
                  >
                    {o.label}
                  </button>
                ))}
              </div>
            </div>

            {/* Industry focus */}
            <div>
              <label className="mb-1.5 block text-sm font-medium text-neutral-800">
                Industry focus{" "}
                <span className="font-normal text-neutral-400">(select all that apply)</span>
              </label>
              <div className="flex flex-wrap gap-2">
                {INDUSTRY_OPTIONS.map((ind) => (
                  <button
                    key={ind}
                    type="button"
                    onClick={() => toggleIndustry(ind)}
                    className={`rounded-full border px-3 py-1 text-xs font-medium transition ${
                      industries.includes(ind)
                        ? "border-indigo-500 bg-indigo-600 text-white"
                        : "border-neutral-300 text-neutral-600 hover:bg-neutral-50"
                    }`}
                  >
                    {humanizeIndustry(ind)}
                  </button>
                ))}
              </div>
            </div>

            {/* Goals */}
            <div>
              <label className="mb-1.5 block text-sm font-medium text-neutral-800">
                Your goals{" "}
                <span className="font-normal text-neutral-400">(one per line)</span>
              </label>
              <textarea
                value={goals}
                onChange={(e) => setGoals(e.target.value)}
                rows={3}
                placeholder={"Ship a RAG pilot\nLearn AI governance"}
                className="w-full rounded-md border border-neutral-300 bg-transparent px-3 py-2 text-sm placeholder:text-neutral-400 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-neutral-900"
              />
            </div>

            <div className="flex items-center justify-end gap-3 pt-2">
              <Button onClick={onSubmit} disabled={saving}>
                {saving && <Loader2 className="h-4 w-4 animate-spin" />}
                Build my path
              </Button>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}

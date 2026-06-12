"use client";

import { useEffect, useState, useSyncExternalStore } from "react";
import Link from "next/link";
import { ArrowRight, BookOpen, GraduationCap, Library, Users, Wrench } from "lucide-react";

import { buttonVariants } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { getDisplayName } from "@/lib/auth";

import { getOnboardingProfile } from "./actions";

const HIGHLIGHTS = [
  { icon: Library, title: "Top assets", desc: "Reference architectures & patterns for your industry." },
  { icon: BookOpen, title: "Learning paths", desc: "Role-tailored ramp-up from the community guild." },
  { icon: Wrench, title: "Key tools", desc: "The frameworks & platforms you'll actually use." },
  { icon: Users, title: "People to know", desc: "Experts matched to your focus areas." },
];

export default function OnboardingLandingPage() {
  const name = useSyncExternalStore(
    () => () => {},
    () => getDisplayName(),
    () => null,
  );
  const [completed, setCompleted] = useState<boolean | null>(null);

  // (The `!name` case is handled in render, so no setState is needed here.)
  useEffect(() => {
    if (!name) return;
    let active = true;
    getOnboardingProfile(name)
      .then((r) => active && setCompleted(Boolean(r.onboarding_completed)))
      .catch(() => active && setCompleted(false));
    return () => {
      active = false;
    };
  }, [name]);

  return (
    <div className="mx-auto max-w-3xl">
      <div className="mb-6">
        <h1 className="flex items-center gap-2 text-2xl font-semibold">
          <GraduationCap className="h-6 w-6 text-indigo-600" />
          Consultant Onboarding
        </h1>
        <p className="mt-1 text-sm text-slate-500">
          Your guided first 30 days on the platform — a personalized path of assets, learning,
          tools, and people, plus a checklist that tracks your progress.
        </p>
      </div>

      <div className="mb-6 grid gap-4 sm:grid-cols-2">
        {HIGHLIGHTS.map((h) => (
          <Card key={h.title}>
            <CardContent className="flex items-start gap-3 pt-6">
              <span className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-indigo-100 text-indigo-600">
                <h.icon className="h-5 w-5" />
              </span>
              <div>
                <h3 className="text-sm font-semibold text-neutral-900">{h.title}</h3>
                <p className="mt-0.5 text-xs text-neutral-500">{h.desc}</p>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      {!name ? (
        <p className="text-sm text-neutral-500">
          Set a display name (log out and back in) to build your onboarding path.
        </p>
      ) : (
        <div className="flex flex-wrap items-center gap-3">
          <Link
            href={completed ? "/modules/onboarding/path" : "/modules/onboarding/profile"}
            className={buttonVariants()}
          >
            {completed ? "View my path" : "Build my path"}
            <ArrowRight className="h-4 w-4" />
          </Link>
          {completed && (
            <Link
              href="/modules/onboarding/profile"
              className={buttonVariants({ variant: "outline" })}
            >
              Edit profile
            </Link>
          )}
        </div>
      )}
    </div>
  );
}

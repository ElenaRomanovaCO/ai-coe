import Link from "next/link";
import { CalendarDays, GraduationCap, MessagesSquare, UsersRound } from "lucide-react";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

import { getCommunityOverview } from "./actions";

export const dynamic = "force-dynamic";

export default async function CommunityHubPage() {
  const overview = await getCommunityOverview();
  const ok = overview.status === "ok";

  const cards = [
    {
      href: "/modules/community/learning",
      icon: GraduationCap,
      title: "Learning Paths",
      desc: "Role- and stage-based paths to build AI delivery skills.",
      count: ok ? overview.learning_paths_count : null,
      unit: "paths",
    },
    {
      href: "/modules/community/office-hours",
      icon: CalendarDays,
      title: "Office Hours",
      desc: "Drop-in clinics with the guild — sign up for upcoming sessions.",
      count: ok ? overview.office_hours_count : null,
      unit: "upcoming",
    },
    {
      href: "/modules/qa",
      icon: MessagesSquare,
      title: "Community Threads",
      desc: "Ask the community and browse answered questions from the Q&A.",
      count: null,
      unit: "",
    },
    {
      href: "/modules/community/experts",
      icon: UsersRound,
      title: "Expert Directory",
      desc: "Find a peer with the right expertise for your engagement.",
      count: ok ? overview.experts_count : null,
      unit: "experts",
    },
  ];

  return (
    <div className="mx-auto max-w-5xl">
      <div className="mb-6">
        <h1 className="flex items-center gap-2 text-2xl font-semibold">
          <UsersRound className="h-6 w-6 text-indigo-600" />
          Community &amp; Enablement Hub
        </h1>
        <p className="mt-1 text-sm text-slate-500">
          Learning paths, office hours, community threads, and an expert directory — everything to
          grow capability and find the right person fast.
        </p>
      </div>

      <div className="grid gap-5 sm:grid-cols-2">
        {cards.map((c) => (
          <Link key={c.href} href={c.href} className="group block">
            <Card className="h-full transition hover:border-indigo-300 hover:shadow-sm">
              <CardHeader>
                <CardTitle className="flex items-center gap-2 text-base">
                  <c.icon className="h-5 w-5 text-indigo-600" />
                  {c.title}
                </CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-sm text-slate-600">{c.desc}</p>
                {c.count !== null && (
                  <p className="mt-3 text-xs font-medium text-indigo-600">
                    {c.count} {c.unit}
                  </p>
                )}
              </CardContent>
            </Card>
          </Link>
        ))}
      </div>
    </div>
  );
}

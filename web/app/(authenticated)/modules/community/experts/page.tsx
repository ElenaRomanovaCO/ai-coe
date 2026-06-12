"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { Search, UsersRound } from "lucide-react";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import type { Expert } from "@/lib/community";

import { getExpertDirectory } from "../actions";

export default function ExpertDirectoryPage() {
  const [expertise, setExpertise] = useState("");
  const [industry, setIndustry] = useState("");
  const [experts, setExperts] = useState<Expert[]>([]);
  const [loaded, setLoaded] = useState(false);

  // Debounce the free-text filters so we don't invoke on every keystroke.
  useEffect(() => {
    const t = setTimeout(() => {
      getExpertDirectory(expertise.trim() || undefined, industry.trim() || undefined)
        .then((r) => setExperts(r.experts ?? []))
        .finally(() => setLoaded(true));
    }, 250);
    return () => clearTimeout(t);
  }, [expertise, industry]);

  return (
    <div className="mx-auto max-w-5xl">
      <nav className="mb-4 text-sm text-slate-500">
        <Link href="/modules/community" className="hover:text-slate-900">
          Community Hub
        </Link>
        <span className="mx-2">/</span>
        <span className="text-slate-700">Expert Directory</span>
      </nav>

      <h1 className="mb-1 flex items-center gap-2 text-2xl font-semibold">
        <UsersRound className="h-6 w-6 text-indigo-600" />
        Expert Directory
      </h1>
      <p className="mb-5 text-sm text-slate-500">
        Find a peer with the right expertise. Filter by topic or industry.
      </p>

      <div className="mb-6 grid gap-3 sm:grid-cols-2">
        <div className="relative">
          <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" />
          <Input
            value={expertise}
            onChange={(e) => setExpertise(e.target.value)}
            placeholder="Expertise — e.g. RAG, governance, agents"
            className="pl-9"
          />
        </div>
        <div className="relative">
          <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" />
          <Input
            value={industry}
            onChange={(e) => setIndustry(e.target.value)}
            placeholder="Industry — e.g. healthcare, financial-services"
            className="pl-9"
          />
        </div>
      </div>

      {!loaded ? (
        <div className="grid gap-4 sm:grid-cols-2">
          {[0, 1, 2, 3].map((i) => (
            <div key={i} className="h-32 animate-pulse rounded-lg bg-slate-100" />
          ))}
        </div>
      ) : experts.length === 0 ? (
        <p className="text-sm text-slate-400">No experts match these filters.</p>
      ) : (
        <div className="grid gap-4 sm:grid-cols-2">
          {experts.map((e) => (
            <Card key={e.id}>
              <CardHeader>
                <CardTitle className="text-base">{e.name}</CardTitle>
                <p className="text-sm text-slate-500">{e.title}</p>
              </CardHeader>
              <CardContent className="space-y-2">
                {e.expertise.length > 0 && (
                  <div className="flex flex-wrap gap-1.5">
                    {e.expertise.map((x, i) => (
                      <span
                        key={i}
                        className="rounded bg-indigo-50 px-2 py-0.5 text-xs font-medium text-indigo-700"
                      >
                        {x}
                      </span>
                    ))}
                  </div>
                )}
                {e.industries.length > 0 && (
                  <p className="text-xs capitalize text-slate-500">
                    {e.industries.map((i) => i.replace(/-/g, " ")).join(", ")}
                  </p>
                )}
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}

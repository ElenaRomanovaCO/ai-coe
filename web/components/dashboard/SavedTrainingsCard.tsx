"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { GraduationCap } from "lucide-react";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import type { TrainingSummary } from "@/lib/trainings";

import { listSavedTrainings } from "@/app/(authenticated)/modules/trainings/actions";

// Self-fetching dashboard card: reads the caller's saved trainings via AGENT-31 so the
// dashboard summary (AGENT-16) doesn't need to know about trainings.
export function SavedTrainingsCard({ name }: { name: string }) {
  const [items, setItems] = useState<TrainingSummary[]>([]);
  const [loaded, setLoaded] = useState(false);

  useEffect(() => {
    let active = true;
    listSavedTrainings(name)
      .then((r) => active && setItems(r.trainings ?? []))
      .finally(() => active && setLoaded(true));
    return () => {
      active = false;
    };
  }, [name]);

  return (
    <Card className="h-full">
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <GraduationCap className="h-4 w-4 text-indigo-600" />
          Saved Trainings
        </CardTitle>
      </CardHeader>
      <CardContent>
        {!loaded ? (
          <div className="space-y-2">
            {[0, 1].map((i) => (
              <div key={i} className="h-8 animate-pulse rounded bg-neutral-100" />
            ))}
          </div>
        ) : items.length === 0 ? (
          <p className="text-sm text-neutral-400">
            No saved trainings yet.{" "}
            <Link href="/modules/trainings" className="text-indigo-600 hover:underline">
              Browse
            </Link>
            .
          </p>
        ) : (
          <ul className="space-y-2">
            {items.slice(0, 5).map((t) => (
              <li key={t.id}>
                <Link
                  href={`/modules/trainings/${t.id}`}
                  className="block truncate text-sm text-neutral-700 hover:text-indigo-700"
                >
                  {t.title}
                </Link>
              </li>
            ))}
          </ul>
        )}
      </CardContent>
    </Card>
  );
}

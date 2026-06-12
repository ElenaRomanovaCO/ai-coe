import { GraduationCap } from "lucide-react";

import { TrainingsBrowser } from "@/components/trainings/TrainingsBrowser";

export default function TrainingsPage() {
  return (
    <div className="mx-auto max-w-6xl">
      <div className="mb-6">
        <h1 className="flex items-center gap-2 text-2xl font-semibold">
          <GraduationCap className="h-6 w-6 text-indigo-600" />
          Trainings
        </h1>
        <p className="mt-1 text-sm text-slate-500">
          CoE-hosted sessions and curated external tutorials, grouped by theme. Browse, filter, open
          the source, and save to your dashboard.
        </p>
      </div>
      <TrainingsBrowser />
    </div>
  );
}

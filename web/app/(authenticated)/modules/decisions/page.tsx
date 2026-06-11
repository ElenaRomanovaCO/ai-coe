import Link from "next/link";
import { BookMarked, Plus } from "lucide-react";

import { DecisionBrowser } from "@/components/decisions/DecisionBrowser";

import { searchDecisions } from "./actions";

export const dynamic = "force-dynamic"; // decisions come from S3 via the module Lambda

export default async function DecisionsPage() {
  const { decisions } = await searchDecisions();

  return (
    <div className="mx-auto max-w-6xl">
      <div className="mb-6 flex items-start justify-between gap-4">
        <div>
          <h1 className="flex items-center gap-2 text-2xl font-semibold">
            <BookMarked className="h-6 w-6 text-indigo-600" />
            Decision Log
          </h1>
          <p className="mt-1 text-sm text-neutral-500">
            {decisions.length} logged engagement decisions. Search across them, or open one to see
            similar past decisions.
          </p>
        </div>
        <Link
          href="/modules/decisions/new"
          className="flex shrink-0 items-center gap-1.5 rounded-md bg-indigo-600 px-3 py-2 text-sm font-medium text-white hover:bg-indigo-700"
        >
          <Plus className="h-4 w-4" />
          Log a decision
        </Link>
      </div>
      <DecisionBrowser decisions={decisions} />
    </div>
  );
}

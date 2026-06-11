import Link from "next/link";
import { notFound } from "next/navigation";

import { IdeationResults } from "@/components/ideation/IdeationResults";

import { getIdeation } from "../actions";

export const dynamic = "force-dynamic";

export default async function IdeationResultPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = await params;
  const res = await getIdeation(id);
  if (res.status !== "ok" || !res.candidates) {
    notFound();
  }

  const req = res.request ?? {};
  const industry = String(req.industry ?? "");
  const stage = req.ai_stage;

  return (
    <div className="mx-auto max-w-6xl">
      <nav className="mb-4 text-sm text-neutral-500">
        <Link href="/modules/ideation" className="hover:text-neutral-900">
          Use Case Ideation
        </Link>
        <span className="mx-2">/</span>
        <span className="text-neutral-700">Results</span>
      </nav>

      <header className="mb-6">
        <h1 className="text-2xl font-semibold">Use case candidates</h1>
        <p className="mt-1 text-sm text-neutral-500">
          {res.candidates.length} candidates
          {industry && <> for <span className="capitalize">{industry.replace(/-/g, " ")}</span></>}
          {stage != null && <> · stage {stage}</>}, ranked by impact vs. effort.
        </p>
      </header>

      <IdeationResults
        candidates={res.candidates}
        markdown={res.markdown ?? ""}
        ideationId={res.ideation_id}
      />
    </div>
  );
}

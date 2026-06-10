import Link from "next/link";

import { ComparisonBuilder } from "@/components/vendor-eval/ComparisonBuilder";

import { listEvaluations } from "../actions";

export const dynamic = "force-dynamic";

export default async function ComparePage() {
  const { evaluations } = await listEvaluations();

  return (
    <div className="mx-auto max-w-5xl">
      <nav className="mb-4 text-sm text-neutral-500">
        <Link href="/modules/vendor-eval" className="hover:text-neutral-900">
          Vendor &amp; Model Evaluation Center
        </Link>
        <span className="mx-2">/</span>
        <span className="text-neutral-700">Build comparison</span>
      </nav>

      <div className="mb-6">
        <h1 className="text-2xl font-semibold">Build a comparison</h1>
        <p className="mt-1 text-sm text-neutral-500">
          Select 2–4 evaluations to put side by side. The center generates a comparison table and
          highlights the key differences, which you can download as markdown.
        </p>
      </div>

      <ComparisonBuilder evaluations={evaluations} />
    </div>
  );
}

import Link from "next/link";
import { notFound } from "next/navigation";

import { ContributeReview } from "@/components/contribute/ContributeReview";

import { getPending } from "../actions";

export const dynamic = "force-dynamic";

export default async function ReviewPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = await params;
  const rec = await getPending(id);
  if (rec.status !== "ok" || !rec.pending_id) notFound();

  return (
    <div className="mx-auto max-w-6xl">
      <nav className="mb-4 text-sm text-slate-500">
        <Link href="/modules/contribute/pending" className="hover:text-slate-900">
          Curator Queue
        </Link>
        <span className="mx-2">/</span>
        <span className="text-slate-700">Review</span>
      </nav>
      <ContributeReview record={rec} />
    </div>
  );
}

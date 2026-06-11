import { MessagesSquare } from "lucide-react";

import { QaBrowser } from "@/components/qa/QaBrowser";

import { listThreads } from "./actions";

export const dynamic = "force-dynamic"; // threads come from S3 via the module Lambda

export default async function QaPage() {
  const { threads } = await listThreads();

  return (
    <div className="mx-auto max-w-5xl">
      <div className="mb-6">
        <h1 className="flex items-center gap-2 text-2xl font-semibold">
          <MessagesSquare className="h-6 w-6 text-indigo-600" />
          Q&amp;A
        </h1>
        <p className="mt-1 text-sm text-neutral-500">
          Ask the community, or get an AI-synthesized answer with citations from across the
          Knowledge Base.
        </p>
      </div>
      <QaBrowser threads={threads} />
    </div>
  );
}

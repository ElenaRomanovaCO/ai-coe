import Link from "next/link";
import { Sparkles } from "lucide-react";

import { AiAsk } from "@/components/qa/AiAsk";

export const dynamic = "force-dynamic";

export default function AskPage() {
  return (
    <div className="mx-auto max-w-3xl">
      <nav className="mb-4 text-sm text-neutral-500">
        <Link href="/modules/qa" className="hover:text-neutral-900">
          Q&amp;A
        </Link>
        <span className="mx-2">/</span>
        <span className="text-neutral-700">Ask AI</span>
      </nav>

      <div className="mb-6">
        <h1 className="flex items-center gap-2 text-2xl font-semibold">
          <Sparkles className="h-6 w-6 text-indigo-600" />
          Ask the Knowledge Base
        </h1>
        <p className="mt-1 text-sm text-neutral-500">
          Get an AI-synthesized answer with citations from across assets, regulations, tools, and
          prior Q&amp;A — then save it as a community thread if it&apos;s worth keeping.
        </p>
      </div>

      <AiAsk />
    </div>
  );
}

import { Sparkles } from "lucide-react";

import { PromptBrowser } from "@/components/prompt-studio/PromptBrowser";

import { listPrompts } from "./actions";

export const dynamic = "force-dynamic"; // prompts come from S3 via the module Lambda

export default async function PromptStudioPage() {
  const { prompts } = await listPrompts();

  return (
    <div className="mx-auto max-w-6xl">
      <div className="mb-6">
        <h1 className="flex items-center gap-2 text-2xl font-semibold">
          <Sparkles className="h-6 w-6 text-indigo-600" />
          Prompt Engineering Studio
        </h1>
        <p className="mt-1 text-sm text-neutral-500">
          {prompts.length} prompts. Author and version prompts, run them live against a model, and
          compare versions side by side.
        </p>
      </div>
      <PromptBrowser prompts={prompts} />
    </div>
  );
}

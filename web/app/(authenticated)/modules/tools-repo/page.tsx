import { Wrench } from "lucide-react";

import { ToolBrowser } from "@/components/tools/ToolBrowser";

import { listTools } from "./actions";

export const dynamic = "force-dynamic"; // tools come from S3 via the module Lambda

export default async function ToolsRepoPage() {
  const { tools } = await listTools();

  return (
    <div className="mx-auto max-w-6xl">
      <div className="mb-6">
        <h1 className="flex items-center gap-2 text-2xl font-semibold">
          <Wrench className="h-6 w-6 text-indigo-600" />
          Skills &amp; Tools Repository
        </h1>
        <p className="mt-1 text-sm text-neutral-500">
          {tools.length} curated AI tools and frameworks — filter by category, stack, stage, or cost
          model, then open one for best-fit guidance and limitations.
        </p>
      </div>
      <ToolBrowser tools={tools} />
    </div>
  );
}

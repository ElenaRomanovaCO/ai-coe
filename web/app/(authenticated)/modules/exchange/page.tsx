import { Puzzle } from "lucide-react";

import { ExchangeBrowser } from "@/components/exchange/ExchangeBrowser";

import { listExchange } from "./actions";

export const dynamic = "force-dynamic"; // entries come from S3 via the module Lambda

export default async function ExchangePage() {
  const { entries } = await listExchange();

  return (
    <div className="mx-auto max-w-6xl">
      <div className="mb-6">
        <h1 className="flex items-center gap-2 text-2xl font-semibold">
          <Puzzle className="h-6 w-6 text-indigo-600" />
          Agentic Skills &amp; Plugin Exchange
        </h1>
        <p className="mt-1 text-sm text-neutral-500">
          {entries.length} reusable agentic-dev artifacts — skills, slash-commands, MCP servers,
          and configs for Claude Code, Cowork, Copilot, and Kiro. Filter by tool and category, or
          open one for install steps.
        </p>
      </div>
      <ExchangeBrowser entries={entries} />
    </div>
  );
}

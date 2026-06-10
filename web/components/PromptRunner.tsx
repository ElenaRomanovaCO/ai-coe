"use client";

import { useState } from "react";
import { Play } from "lucide-react";

import { runPrompt } from "@/app/(authenticated)/modules/prompt-studio/actions";
import { MarkdownRenderer } from "@/components/MarkdownRenderer";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { MODEL_OPTIONS, lastRunKey, type RunResult } from "@/lib/prompts";
import { cn } from "@/lib/utils";

const SELECT_CLASS =
  "w-full rounded-md border border-neutral-300 bg-white px-3 py-2 text-sm text-neutral-900 focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500";

// Live runner: substitute variable values, call AGENT-11 run_prompt (non-streaming),
// show the output + a metrics row. The last output is stashed in sessionStorage so the
// diff page can show side-by-side last outputs.
export function PromptRunner({
  promptId,
  promptText,
  variableNames,
  defaultModel,
}: {
  promptId: string;
  promptText: string;
  variableNames: string[];
  defaultModel: string;
}) {
  const [model, setModel] = useState(defaultModel);
  const [maxTokens, setMaxTokens] = useState(1000);
  const [temperature, setTemperature] = useState(0.7);
  const [values, setValues] = useState<Record<string, string>>({});
  const [running, setRunning] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<RunResult | null>(null);

  async function onRun() {
    if (!promptText.trim() || running) return;
    setRunning(true);
    setError(null);
    try {
      // Only send values for variables currently referenced (stale keys are ignored).
      const vars = Object.fromEntries(variableNames.map((v) => [v, values[v] ?? ""]));
      const res = await runPrompt({
        prompt_text: promptText,
        variables: vars,
        model_id: model,
        max_tokens: maxTokens,
        temperature,
      });
      if (res.status === "ok") {
        setResult(res);
        try {
          sessionStorage.setItem(
            lastRunKey(promptId),
            JSON.stringify({ output: res.output, model_id: res.model_id }),
          );
        } catch {
          /* storage may be unavailable; non-fatal */
        }
      } else {
        setError(res.message || "The run failed.");
      }
    } catch {
      setError("Something went wrong running the prompt. Please try again.");
    } finally {
      setRunning(false);
    }
  }

  return (
    <div className="space-y-4">
      <div className="grid grid-cols-2 gap-3">
        <div className="col-span-2">
          <label className="mb-1 block text-xs font-medium text-neutral-600">Model</label>
          <select className={SELECT_CLASS} value={model} onChange={(e) => setModel(e.target.value)}>
            {MODEL_OPTIONS.map((m) => (
              <option key={m.value} value={m.value}>
                {m.label}
                {m.note ? ` — ${m.note}` : ""}
              </option>
            ))}
          </select>
        </div>
        <div>
          <label className="mb-1 block text-xs font-medium text-neutral-600">Max tokens</label>
          <Input
            type="number"
            value={maxTokens}
            min={1}
            max={4096}
            onChange={(e) => setMaxTokens(Number(e.target.value) || 1000)}
          />
        </div>
        <div>
          <label className="mb-1 block text-xs font-medium text-neutral-600">
            Temperature ({temperature.toFixed(1)})
          </label>
          <input
            type="range"
            min={0}
            max={1}
            step={0.1}
            value={temperature}
            onChange={(e) => setTemperature(Number(e.target.value))}
            className="mt-2 w-full"
          />
        </div>
      </div>

      {variableNames.length > 0 && (
        <div className="space-y-2">
          <p className="text-xs font-medium uppercase tracking-wide text-neutral-500">Variables</p>
          {variableNames.map((v) => (
            <div key={v}>
              <label className="mb-1 block text-xs text-neutral-500">{v}</label>
              <Input
                value={values[v] ?? ""}
                onChange={(e) => setValues((prev) => ({ ...prev, [v]: e.target.value }))}
                placeholder={`{{${v}}}`}
              />
            </div>
          ))}
        </div>
      )}

      <Button onClick={onRun} disabled={running || !promptText.trim()} className="w-full">
        <Play className="h-4 w-4" />
        {running ? "Running…" : "Run prompt"}
      </Button>

      {error && <p className="text-sm text-red-600">{error}</p>}

      {result && (
        <div className="space-y-2">
          <div className="flex flex-wrap gap-x-4 gap-y-1 text-[11px] text-neutral-500">
            <span>in {result.tokens_in} tok</span>
            <span>out {result.tokens_out} tok</span>
            <span>${result.cost_usd.toFixed(5)}</span>
            <span>{result.latency_ms} ms</span>
          </div>
          <div className={cn("rounded-lg border border-neutral-200 bg-neutral-50 p-3")}>
            <MarkdownRenderer>{result.output}</MarkdownRenderer>
          </div>
        </div>
      )}
    </div>
  );
}

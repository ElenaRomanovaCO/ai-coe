import Link from "next/link";
import { notFound } from "next/navigation";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { formatUsd, paybackLabel, roiBand } from "@/lib/roi";
import { cn } from "@/lib/utils";

import { getRoi } from "../actions";

export const dynamic = "force-dynamic";

export default async function RoiResultPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = await params;
  const res = await getRoi(id);
  if (res.status !== "ok" || !res.result) {
    notFound();
  }

  const { inputs, result } = res;
  // Bar widths for the cost-vs-value comparison.
  const maxVal = Math.max(result.total_cost_usd, result.annual_value_usd * (inputs.horizon_years || 1), 1);
  const costPct = Math.round((result.total_cost_usd / maxVal) * 100);
  const valuePct = Math.round(((result.annual_value_usd * (inputs.horizon_years || 1)) / maxVal) * 100);

  return (
    <div className="mx-auto max-w-5xl">
      <nav className="mb-4 text-sm text-neutral-500">
        <Link href="/modules/roi-calculator" className="hover:text-neutral-900">
          ROI Calculator
        </Link>
        <span className="mx-2">/</span>
        <span className="text-neutral-700">{inputs.project_name || "Result"}</span>
      </nav>

      <header className="mb-6">
        <h1 className="text-2xl font-semibold">{inputs.project_name || "AI Project"}</h1>
        <p className="mt-1 text-sm capitalize text-neutral-500">
          {inputs.industry ? inputs.industry.replace(/-/g, " ") : "—"} · {inputs.horizon_years}-year
          horizon
        </p>
      </header>

      {/* Headline metrics */}
      <div className="mb-8 grid grid-cols-2 gap-4 lg:grid-cols-4">
        <Metric label="ROI" value={`${result.roi_pct.toFixed(1)}%`} className={roiBand(result.roi_pct)} />
        <Metric label="Payback" value={paybackLabel(result.payback_months)} />
        <Metric label="Total cost" value={formatUsd(result.total_cost_usd)} />
        <Metric label="Net value" value={formatUsd(result.net_value_usd)} className={roiBand(result.roi_pct)} />
      </div>

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Cost vs. value (over horizon)</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <Bar label="Total cost" amount={formatUsd(result.total_cost_usd)} pct={costPct} color="bg-red-400" />
            <Bar
              label={`Value (${inputs.horizon_years}yr)`}
              amount={formatUsd(result.annual_value_usd * (inputs.horizon_years || 1))}
              pct={valuePct}
              color="bg-green-500"
            />
            <p className="pt-2 text-xs text-neutral-500">
              Annual value {formatUsd(result.annual_value_usd)} · annual run cost{" "}
              {formatUsd(inputs.run_cost_usd_yr)} · build {formatUsd(inputs.build_cost_usd)}
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="text-base">Business case</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="whitespace-pre-wrap text-sm leading-relaxed text-neutral-700">
              {result.narrative}
            </p>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}

function Metric({ label, value, className }: { label: string; value: string; className?: string }) {
  return (
    <div className="rounded-lg border border-neutral-200 p-4">
      <p className="text-xs uppercase tracking-wide text-neutral-500">{label}</p>
      <p className={cn("mt-1 text-xl font-semibold text-neutral-900", className)}>{value}</p>
    </div>
  );
}

function Bar({ label, amount, pct, color }: { label: string; amount: string; pct: number; color: string }) {
  return (
    <div>
      <div className="mb-1 flex items-center justify-between text-xs text-neutral-600">
        <span>{label}</span>
        <span className="font-medium">{amount}</span>
      </div>
      <div className="h-3 w-full overflow-hidden rounded-full bg-neutral-100">
        <div className={cn("h-full rounded-full", color)} style={{ width: `${Math.max(2, pct)}%` }} />
      </div>
    </div>
  );
}

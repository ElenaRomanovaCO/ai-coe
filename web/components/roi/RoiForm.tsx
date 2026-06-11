"use client";

import { useState, useSyncExternalStore, useTransition } from "react";
import { useRouter } from "next/navigation";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { getDisplayName } from "@/lib/auth";
import { INDUSTRIES } from "@/lib/roi";

import { calculateRoi } from "@/app/(authenticated)/modules/roi-calculator/actions";

export function RoiForm() {
  const name = useSyncExternalStore(
    () => () => {},
    () => getDisplayName(),
    () => null,
  );

  const router = useRouter();
  const [projectName, setProjectName] = useState("");
  const [industry, setIndustry] = useState("healthcare");
  const [buildCost, setBuildCost] = useState(100000);
  const [runCost, setRunCost] = useState(20000);
  const [teamSize, setTeamSize] = useState(4);
  const [durationWeeks, setDurationWeeks] = useState(12);
  const [hoursSaved, setHoursSaved] = useState(2000);
  const [hourlyRate, setHourlyRate] = useState(80);
  const [revenueUplift, setRevenueUplift] = useState(0);
  const [otherBenefit, setOtherBenefit] = useState(0);
  const [horizon, setHorizon] = useState(3);
  const [error, setError] = useState<string | null>(null);
  const [pending, startTransition] = useTransition();

  function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    if (!projectName.trim()) {
      setError("A project name is required.");
      return;
    }
    startTransition(async () => {
      const res = await calculateRoi({
        display_name: name ?? "Guest",
        project_name: projectName.trim(),
        industry,
        build_cost_usd: buildCost,
        run_cost_usd_yr: runCost,
        team_size: teamSize,
        duration_weeks: durationWeeks,
        hours_saved_yr: hoursSaved,
        loaded_hourly_rate_usd: hourlyRate,
        revenue_uplift_usd_yr: revenueUplift,
        other_benefit_usd_yr: otherBenefit,
        horizon_years: horizon,
      });
      if (res.status === "ok" && res.roi_id) {
        router.push(`/modules/roi-calculator/${res.roi_id}`);
      } else {
        setError(res.message || "Couldn't compute ROI. Please try again.");
      }
    });
  }

  return (
    <form onSubmit={onSubmit} className="grid grid-cols-1 gap-6 lg:grid-cols-2">
      <Card>
        <CardHeader>
          <CardTitle className="text-base">Project</CardTitle>
        </CardHeader>
        <CardContent className="space-y-3">
          <Field label="Project name">
            <Input value={projectName} onChange={(e) => setProjectName(e.target.value)} placeholder="Doc Processing Assistant" />
          </Field>
          <Field label="Industry">
            <select
              value={industry}
              onChange={(e) => setIndustry(e.target.value)}
              className="flex h-10 w-full rounded-md border border-neutral-300 bg-transparent px-3 text-sm capitalize"
            >
              {INDUSTRIES.map((i) => (
                <option key={i} value={i}>{i.replace(/-/g, " ")}</option>
              ))}
            </select>
          </Field>
          <div className="flex gap-3">
            <Num label="Team size" value={teamSize} onChange={setTeamSize} />
            <Num label="Duration (weeks)" value={durationWeeks} onChange={setDurationWeeks} />
            <Num label="Horizon (years)" value={horizon} onChange={setHorizon} min={1} max={10} />
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="text-base">Costs (USD)</CardTitle>
        </CardHeader>
        <CardContent className="space-y-3">
          <Num label="One-time build / delivery" value={buildCost} onChange={setBuildCost} wide />
          <Num label="Annual run / licensing / infra" value={runCost} onChange={setRunCost} wide />
        </CardContent>
      </Card>

      <Card className="lg:col-span-2">
        <CardHeader>
          <CardTitle className="text-base">Value drivers (annualized, USD)</CardTitle>
        </CardHeader>
        <CardContent className="grid grid-cols-1 gap-3 sm:grid-cols-2">
          <Num label="Hours saved / year" value={hoursSaved} onChange={setHoursSaved} wide />
          <Num label="Loaded hourly rate" value={hourlyRate} onChange={setHourlyRate} wide />
          <Num label="Revenue uplift / year" value={revenueUplift} onChange={setRevenueUplift} wide />
          <Num label="Other benefit / year" value={otherBenefit} onChange={setOtherBenefit} wide />
        </CardContent>
      </Card>

      <div className="lg:col-span-2">
        {error && <p className="mb-2 text-sm text-red-600">{error}</p>}
        <Button type="submit" disabled={pending} className="bg-indigo-600 hover:bg-indigo-700">
          {pending ? "Computing…" : "Calculate ROI"}
        </Button>
      </div>
    </form>
  );
}

function Field({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div className="flex-1">
      <label className="mb-1 block text-sm font-medium text-neutral-700">{label}</label>
      {children}
    </div>
  );
}

function Num({
  label,
  value,
  onChange,
  min = 0,
  max,
  wide,
}: {
  label: string;
  value: number;
  onChange: (v: number) => void;
  min?: number;
  max?: number;
  wide?: boolean;
}) {
  return (
    <div className={wide ? "flex-1" : "flex-1"}>
      <label className="mb-1 block text-sm font-medium text-neutral-700">{label}</label>
      <Input
        type="number"
        min={min}
        max={max}
        value={value}
        onChange={(e) => onChange(Number(e.target.value))}
      />
    </div>
  );
}

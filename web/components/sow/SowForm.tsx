"use client";

import { useState, useSyncExternalStore, useTransition } from "react";
import { useRouter } from "next/navigation";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { getDisplayName } from "@/lib/auth";
import { ENGAGEMENT_TYPES, PRICING_MODELS, toList } from "@/lib/sow";

import { generateSow } from "@/app/(authenticated)/modules/sow-generator/actions";

export function SowForm() {
  const name = useSyncExternalStore(
    () => () => {},
    () => getDisplayName(),
    () => null,
  );

  const router = useRouter();
  const [clientContext, setClientContext] = useState("");
  const [engagementType, setEngagementType] = useState("pilot");
  const [objectives, setObjectives] = useState("");
  const [scopeItems, setScopeItems] = useState("");
  const [deliverables, setDeliverables] = useState("");
  const [timelineWeeks, setTimelineWeeks] = useState(6);
  const [milestones, setMilestones] = useState("");
  const [pricingModel, setPricingModel] = useState("fixed");
  const [assumptions, setAssumptions] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [pending, startTransition] = useTransition();

  function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    if (!clientContext.trim() && !objectives.trim() && !deliverables.trim()) {
      setError("Add at least the client context, objectives, or deliverables.");
      return;
    }
    startTransition(async () => {
      const res = await generateSow({
        display_name: name ?? "Guest",
        client_context: clientContext.trim(),
        engagement_type: engagementType,
        objectives: toList(objectives),
        scope_items: toList(scopeItems),
        deliverables: toList(deliverables),
        timeline_weeks: timelineWeeks,
        milestones: toList(milestones),
        pricing_model: pricingModel,
        assumptions: toList(assumptions),
      });
      if (res.status === "ok" && res.sow_id) {
        router.push(`/modules/sow-generator/${res.sow_id}`);
      } else {
        setError(res.message || "Couldn't generate the SOW. Please try again.");
      }
    });
  }

  return (
    <form onSubmit={onSubmit} className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle className="text-base">Engagement</CardTitle>
        </CardHeader>
        <CardContent className="space-y-3">
          <Field label="Client context">
            <Input
              value={clientContext}
              onChange={(e) => setClientContext(e.target.value)}
              placeholder="A fintech scaling fraud detection across new markets"
            />
          </Field>
          <div className="flex gap-3">
            <Field label="Engagement type">
              <Select value={engagementType} onChange={setEngagementType} options={ENGAGEMENT_TYPES} />
            </Field>
            <Field label="Pricing model">
              <Select value={pricingModel} onChange={setPricingModel} options={PRICING_MODELS} />
            </Field>
            <Field label="Timeline (weeks)">
              <Input
                type="number"
                min={1}
                value={timelineWeeks}
                onChange={(e) => setTimelineWeeks(Number(e.target.value))}
              />
            </Field>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="text-base">Scope &amp; deliverables</CardTitle>
        </CardHeader>
        <CardContent className="grid grid-cols-1 gap-3 sm:grid-cols-2">
          <Field label="Objectives" hint="one per line">
            <Area value={objectives} onChange={setObjectives} placeholder={"reduce fraud losses"} />
          </Field>
          <Field label="Scope items" hint="one per line">
            <Area value={scopeItems} onChange={setScopeItems} placeholder={"data prep\nmodel training"} />
          </Field>
          <Field label="Deliverables" hint="one per line">
            <Area value={deliverables} onChange={setDeliverables} placeholder={"scored API\neval report"} />
          </Field>
          <Field label="Milestones" hint="one per line">
            <Area value={milestones} onChange={setMilestones} placeholder={"week 2: data ready"} />
          </Field>
          <Field label="Assumptions" hint="one per line">
            <Area value={assumptions} onChange={setAssumptions} placeholder={"client SME available"} />
          </Field>
        </CardContent>
      </Card>

      {error && <p className="text-sm text-red-600">{error}</p>}
      <Button type="submit" disabled={pending} className="bg-indigo-600 hover:bg-indigo-700">
        {pending ? "Drafting SOW…" : "Generate SOW"}
      </Button>
    </form>
  );
}

function Field({ label, hint, children }: { label: string; hint?: string; children: React.ReactNode }) {
  return (
    <div className="flex-1">
      <label className="mb-1 block text-sm font-medium text-neutral-700">
        {label}
        {hint && <span className="ml-2 text-xs font-normal text-neutral-400">{hint}</span>}
      </label>
      {children}
    </div>
  );
}

function Select({
  value,
  onChange,
  options,
}: {
  value: string;
  onChange: (v: string) => void;
  options: string[];
}) {
  return (
    <select
      value={value}
      onChange={(e) => onChange(e.target.value)}
      className="flex h-10 w-full rounded-md border border-neutral-300 bg-transparent px-3 text-sm capitalize"
    >
      {options.map((o) => (
        <option key={o} value={o}>{o}</option>
      ))}
    </select>
  );
}

function Area({
  value,
  onChange,
  placeholder,
}: {
  value: string;
  onChange: (v: string) => void;
  placeholder?: string;
}) {
  return (
    <textarea
      value={value}
      onChange={(e) => onChange(e.target.value)}
      placeholder={placeholder}
      rows={3}
      className="w-full rounded-md border border-neutral-300 bg-transparent px-3 py-2 text-sm placeholder:text-neutral-400"
    />
  );
}

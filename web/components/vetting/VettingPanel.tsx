"use client";

import { useState, useSyncExternalStore, useTransition } from "react";
import { useRouter } from "next/navigation";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { VettingChecklist } from "@/components/vetting/VettingChecklist";
import { getDisplayName } from "@/lib/auth";
import {
  APPROVAL_STATUSES,
  CONTEXT_INDUSTRIES,
  DATA_SENSITIVITIES,
  RISK_STYLE,
  riskLabel,
  type AssessResult,
  type VettingRecord,
} from "@/lib/vendorVetting";
import { cn } from "@/lib/utils";

import { assessVendor, setVendorStatus } from "@/app/(authenticated)/modules/vendor-vetting/actions";

// Interactive vetting: run the deterministic assessment (with context) and record the
// team-wide approval status. Seeded with the vendor's current vetting record.
export function VettingPanel({
  vendorId,
  initial,
}: {
  vendorId: string;
  initial: VettingRecord;
}) {
  const name = useSyncExternalStore(
    () => () => {},
    () => getDisplayName(),
    () => null,
  );
  const router = useRouter();

  const [industry, setIndustry] = useState("");
  const [sensitivity, setSensitivity] = useState("internal");
  const [result, setResult] = useState<AssessResult | null>(null);
  const [assessing, startAssess] = useTransition();

  const [status, setStatus] = useState<string>(
    initial.approval_status === "unvetted" ? "approved" : initial.approval_status,
  );
  const [note, setNote] = useState(initial.note ?? "");
  const [saved, setSaved] = useState(false);
  const [savingStatus, startSave] = useTransition();

  // Show the latest assessment: the just-run one, else the persisted record.
  const tier = result?.risk_tier ?? initial.risk_tier;
  const controls = result?.controls ?? initial.controls;
  const gaps = result?.gaps ?? initial.gaps;
  const narrative = result?.narrative ?? initial.narrative;

  function onAssess() {
    startAssess(async () => {
      const res = await assessVendor(vendorId, industry, sensitivity);
      if (res.status === "ok") setResult(res);
    });
  }

  function onSaveStatus() {
    setSaved(false);
    startSave(async () => {
      const res = await setVendorStatus(vendorId, status, note.trim(), name ?? "Guest");
      if (res.status === "ok") {
        setSaved(true);
        router.refresh(); // update the header badge
      }
    });
  }

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center justify-between text-base">
            Vetting assessment
            {tier && (
              <span className={cn("rounded border px-2 py-0.5 text-xs font-medium uppercase", RISK_STYLE[tier])}>
                {riskLabel(tier)}
              </span>
            )}
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex flex-wrap items-end gap-2">
            <label className="text-xs text-neutral-600">
              Context industry
              <select
                value={industry}
                onChange={(e) => setIndustry(e.target.value)}
                className="mt-1 block rounded border border-neutral-300 bg-white px-2 py-1 text-sm capitalize"
              >
                {CONTEXT_INDUSTRIES.map((i) => (
                  <option key={i} value={i}>{i ? i.replace(/-/g, " ") : "general"}</option>
                ))}
              </select>
            </label>
            <label className="text-xs text-neutral-600">
              Data sensitivity
              <select
                value={sensitivity}
                onChange={(e) => setSensitivity(e.target.value)}
                className="mt-1 block rounded border border-neutral-300 bg-white px-2 py-1 text-sm uppercase"
              >
                {DATA_SENSITIVITIES.map((s) => (
                  <option key={s} value={s}>{s}</option>
                ))}
              </select>
            </label>
            <Button onClick={onAssess} size="sm" disabled={assessing} className="bg-indigo-600 hover:bg-indigo-700">
              {assessing ? "Scoring…" : "Run assessment"}
            </Button>
          </div>

          {narrative && (
            <p className="rounded-md bg-neutral-50 p-3 text-sm text-neutral-700">{narrative}</p>
          )}
          {gaps.length > 0 && (
            <p className="text-xs text-red-600">Gaps: {gaps.join(" · ")}</p>
          )}
          <VettingChecklist controls={controls} />
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="text-base">Approval status</CardTitle>
        </CardHeader>
        <CardContent className="space-y-3">
          <div className="flex flex-wrap items-end gap-2">
            <select
              value={status}
              onChange={(e) => setStatus(e.target.value)}
              className="rounded border border-neutral-300 bg-white px-2 py-1 text-sm capitalize"
            >
              {APPROVAL_STATUSES.map((s) => (
                <option key={s} value={s}>{s}</option>
              ))}
            </select>
            <Input
              value={note}
              onChange={(e) => setNote(e.target.value)}
              placeholder="Note (e.g. approved for non-PHI use)"
              className="min-w-[16rem] flex-1"
            />
            <Button onClick={onSaveStatus} size="sm" disabled={savingStatus} variant="outline">
              {savingStatus ? "Saving…" : "Set status"}
            </Button>
          </div>
          {saved && <p className="text-xs text-green-700">Saved — visible team-wide.</p>}
        </CardContent>
      </Card>
    </div>
  );
}

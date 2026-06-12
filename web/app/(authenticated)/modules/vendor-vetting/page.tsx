import Link from "next/link";
import { BadgeCheck } from "lucide-react";

import {
  RISK_STYLE,
  STATUS_STYLE,
  riskLabel,
  type VendorSummary,
} from "@/lib/vendorVetting";
import { cn } from "@/lib/utils";

import { listVendors } from "./actions";

export const dynamic = "force-dynamic"; // vendors + sidecars come from S3 via the Lambda

export default async function VendorVettingPage() {
  const { vendors } = await listVendors();

  return (
    <div className="mx-auto max-w-6xl">
      <div className="mb-6">
        <h1 className="flex items-center gap-2 text-2xl font-semibold">
          <BadgeCheck className="h-6 w-6 text-indigo-600" />
          Vendor Vetting
        </h1>
        <p className="mt-1 text-sm text-neutral-500">
          Security &amp; compliance risk and approval status for AI vendors. (For capability
          comparison, see Benchmarks.) Open a vendor to run a vetting assessment and set its
          approval status.
        </p>
      </div>

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {vendors.map((v) => (
          <VendorCard key={v.vendor_id} vendor={v} />
        ))}
      </div>
    </div>
  );
}

function VendorCard({ vendor: v }: { vendor: VendorSummary }) {
  return (
    <Link
      href={`/modules/vendor-vetting/${v.vendor_id}`}
      className="flex flex-col rounded-lg border border-neutral-200 p-4 transition-colors hover:border-indigo-300 hover:bg-neutral-50"
    >
      <div className="mb-2 flex flex-wrap items-center gap-2">
        <span
          className={cn(
            "rounded border px-1.5 py-0.5 text-[10px] font-medium uppercase",
            v.risk_tier ? RISK_STYLE[v.risk_tier] : "border-neutral-200 bg-neutral-100 text-neutral-500",
          )}
        >
          {riskLabel(v.risk_tier)}
        </span>
        <span
          className={cn(
            "rounded border px-1.5 py-0.5 text-[10px] font-medium uppercase",
            STATUS_STYLE[v.approval_status],
          )}
        >
          {v.approval_status}
        </span>
      </div>
      <p className="text-sm font-medium capitalize text-neutral-900">
        {v.category.replace(/-/g, " ")}
      </p>
      {v.vendors_compared.length > 0 && (
        <p className="mt-1 truncate text-xs text-neutral-500">{v.vendors_compared.join(" · ")}</p>
      )}
      <p className="mt-2 text-[11px] text-neutral-400">Verified {v.last_verified.slice(0, 10)}</p>
    </Link>
  );
}

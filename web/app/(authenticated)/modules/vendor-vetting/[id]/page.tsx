import Link from "next/link";
import { notFound } from "next/navigation";

import { AssetChatPanelHook } from "@/components/AssetChatPanelHook";
import { MarkdownRenderer } from "@/components/MarkdownRenderer";
import { VettingPanel } from "@/components/vetting/VettingPanel";
import { RISK_STYLE, STATUS_STYLE, riskLabel } from "@/lib/vendorVetting";
import { cn } from "@/lib/utils";

import { getVendor } from "../actions";

export const dynamic = "force-dynamic";

export default async function VendorVettingDetailPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = await params;
  const res = await getVendor(id);
  if (res.status !== "ok" || !res.vendor) {
    notFound();
  }

  const v = res.vendor;
  const vetting = res.vetting;

  return (
    <div className="mx-auto max-w-6xl">
      <nav className="mb-4 text-sm text-neutral-500">
        <Link href="/modules/vendor-vetting" className="hover:text-neutral-900">
          Vendor Vetting
        </Link>
        <span className="mx-2">/</span>
        <span className="capitalize text-neutral-700">{v.category.replace(/-/g, " ")}</span>
      </nav>

      <header className="mb-6 flex flex-wrap items-start justify-between gap-3">
        <div>
          <h1 className="text-2xl font-semibold capitalize">{v.category.replace(/-/g, " ")}</h1>
          {v.vendors_compared.length > 0 && (
            <p className="mt-1 text-sm text-neutral-500">{v.vendors_compared.join(" · ")}</p>
          )}
        </div>
        <div className="flex flex-wrap items-center gap-2 text-xs">
          {vetting.risk_tier && (
            <span className={cn("rounded border px-2 py-0.5 font-medium uppercase", RISK_STYLE[vetting.risk_tier])}>
              {riskLabel(vetting.risk_tier)}
            </span>
          )}
          <span className={cn("rounded border px-2 py-0.5 font-medium uppercase", STATUS_STYLE[vetting.approval_status])}>
            {vetting.approval_status}
          </span>
        </div>
      </header>

      <div className="flex flex-col gap-8 lg:flex-row">
        <div className="min-w-0 flex-1">
          <VettingPanel vendorId={v.vendor_id} initial={vetting} />
        </div>

        <aside className="w-full shrink-0 space-y-6 lg:w-80">
          <AssetChatPanelHook
            assetId={v.vendor_id}
            assetTitle={v.category.replace(/-/g, " ")}
            assetContent={v.body_markdown}
            assetFrontmatter={v.frontmatter}
          />
          <section className="rounded-lg border border-neutral-200 p-4">
            <h2 className="mb-2 text-sm font-semibold">Vendor profile</h2>
            <div className="prose-sm">
              <MarkdownRenderer>{v.body_markdown}</MarkdownRenderer>
            </div>
          </section>
        </aside>
      </div>
    </div>
  );
}

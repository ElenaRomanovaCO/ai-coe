import { ClipboardCheck } from "lucide-react";

import { RegulationBrowser } from "@/components/compliance/RegulationBrowser";

import { listRegulations } from "./actions";

export const dynamic = "force-dynamic"; // regs come from S3 via the module Lambda

export default async function ComplianceTrackerPage() {
  const { regulations } = await listRegulations();

  return (
    <div className="mx-auto max-w-6xl">
      <div className="mb-6">
        <h1 className="flex items-center gap-2 text-2xl font-semibold">
          <ClipboardCheck className="h-6 w-6 text-indigo-600" />
          Compliance Tracker
        </h1>
        <p className="mt-1 text-sm text-neutral-500">
          Browse {regulations.length} AI regulations across geographies and industries. Open one to
          read it and ask questions, or apply it to a specific use case.
        </p>
      </div>
      <RegulationBrowser regulations={regulations} />
    </div>
  );
}

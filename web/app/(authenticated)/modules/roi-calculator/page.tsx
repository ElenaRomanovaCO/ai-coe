import { Calculator } from "lucide-react";

import { RoiForm } from "@/components/roi/RoiForm";

export default function RoiCalculatorPage() {
  return (
    <div className="mx-auto max-w-5xl">
      <div className="mb-6">
        <h1 className="flex items-center gap-2 text-2xl font-semibold">
          <Calculator className="h-6 w-6 text-indigo-600" />
          AI Project ROI Calculator
        </h1>
        <p className="mt-1 text-sm text-neutral-500">
          Enter an AI project&apos;s costs and value drivers for a defensible estimate — total cost,
          annual value, ROI %, payback period, and a short business case. The numbers are computed
          deterministically; the narrative is generated from them.
        </p>
      </div>
      <RoiForm />
    </div>
  );
}

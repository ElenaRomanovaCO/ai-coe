import Link from "next/link";
import { Boxes, GitCompare } from "lucide-react";

import { VendorEvalBrowser } from "@/components/vendor-eval/VendorEvalBrowser";
import { Button } from "@/components/ui/button";

import { listEvaluations } from "./actions";

export const dynamic = "force-dynamic"; // evaluations come from S3 via the module Lambda

export default async function VendorEvalPage() {
  const { evaluations } = await listEvaluations();

  return (
    <div className="mx-auto max-w-6xl">
      <div className="mb-6 flex items-start justify-between gap-4">
        <div>
          <h1 className="flex items-center gap-2 text-2xl font-semibold">
            <Boxes className="h-6 w-6 text-indigo-600" />
            Vendor &amp; Model Evaluation Center
          </h1>
          <p className="mt-1 text-sm text-neutral-500">
            {evaluations.length} structured evaluations of AI vendors, models, and platforms. Open
            one, or build a custom side-by-side comparison.
          </p>
        </div>
        <Link href="/modules/vendor-eval/compare">
          <Button>
            <GitCompare className="h-4 w-4" />
            Build comparison
          </Button>
        </Link>
      </div>
      <VendorEvalBrowser evaluations={evaluations} />
    </div>
  );
}

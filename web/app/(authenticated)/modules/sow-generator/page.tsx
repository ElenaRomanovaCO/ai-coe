import { FileSignature } from "lucide-react";

import { SowForm } from "@/components/sow/SowForm";

export default function SowGeneratorPage() {
  return (
    <div className="mx-auto max-w-4xl">
      <div className="mb-6">
        <h1 className="flex items-center gap-2 text-2xl font-semibold">
          <FileSignature className="h-6 w-6 text-indigo-600" />
          AI SOW Generator
        </h1>
        <p className="mt-1 text-sm text-neutral-500">
          Generate a draft Statement of Work from engagement context — objectives, scope,
          deliverables, timeline, pricing, assumptions, and acceptance criteria — to review, edit,
          and export. Structured inputs are placed verbatim; the prose is drafted from them.
        </p>
      </div>
      <SowForm />
    </div>
  );
}

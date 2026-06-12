import Link from "next/link";
import { notFound } from "next/navigation";

import { ReportEditor } from "@/components/reports/ReportEditor";

import { getReport } from "../actions";

export const dynamic = "force-dynamic";

export default async function ReportPage({
  params,
}: {
  params: Promise<{ report_id: string }>;
}) {
  const { report_id } = await params;
  const res = await getReport(report_id);
  if (res.status !== "ok" || !res.section_order?.length) {
    notFound();
  }

  return (
    <div className="mx-auto max-w-6xl">
      <nav className="mb-4 text-sm text-slate-500">
        <Link href="/modules/reports" className="hover:text-slate-900">
          Client Reports
        </Link>
        <span className="mx-2">/</span>
        <span className="text-slate-700">{res.title}</span>
      </nav>
      <ReportEditor report={res} />
    </div>
  );
}

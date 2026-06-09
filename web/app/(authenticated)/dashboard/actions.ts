"use server";

// Dashboard server action: one call to AGENT-16 returns the full DashboardSummary.
// Invoked from the client page (display_name is client-side). Under (authenticated),
// so the proxy middleware already gates unauthenticated callers.

import { invokeModule } from "@/lib/aws";
import type { DashboardSummary } from "@/lib/dashboard";

const DASHBOARD_AGENT_ID = "AGENT-16";

export async function getDashboardSummary(displayName: string): Promise<DashboardSummary> {
  return invokeModule<DashboardSummary>(DASHBOARD_AGENT_ID, {
    op: "summary",
    display_name: displayName,
  });
}

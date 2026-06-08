import Link from "next/link";

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";

export default function DashboardPage() {
  return (
    <div className="mx-auto flex max-w-3xl flex-col gap-4">
      <div>
        <h1 className="text-2xl font-semibold">Dashboard</h1>
        <p className="text-sm text-neutral-500">
          Placeholder for the authenticated experience. Modules land here in later waves.
        </p>
      </div>
      <div className="grid gap-4 sm:grid-cols-2">
        <Link href="/modules/asset-library" className="block">
          <Card className="h-full transition-colors hover:border-neutral-400 hover:bg-neutral-50">
            <CardHeader>
              <CardTitle>Asset Library</CardTitle>
              <CardDescription>Browse curated AI delivery assets.</CardDescription>
            </CardHeader>
            <CardContent className="text-sm text-neutral-500">Open →</CardContent>
          </Card>
        </Link>
        <Card>
          <CardHeader>
            <CardTitle>Chat</CardTitle>
            <CardDescription>Front-door orchestrator (built in wave 1).</CardDescription>
          </CardHeader>
          <CardContent className="text-sm text-neutral-500">Use the dock, bottom-right.</CardContent>
        </Card>
        <Card>
          <CardHeader>
            <CardTitle>Knowledge Base</CardTitle>
            <CardDescription>Auto-embedded markdown vault.</CardDescription>
          </CardHeader>
          <CardContent className="text-sm text-neutral-500">Coming soon.</CardContent>
        </Card>
      </div>
    </div>
  );
}

import Link from "next/link";

import { Button, buttonVariants } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

// "Browse Assets" is live (Module 2). The others are disabled until their modules
// land (Maturity Assessment = Module 1, Kit Builder = Module 3).
export function QuickActionsCard() {
  return (
    <Card className="h-full">
      <CardHeader>
        <CardTitle>Quick Actions</CardTitle>
      </CardHeader>
      <CardContent className="flex flex-col gap-2">
        <Link href="/modules/asset-library" className={buttonVariants({ size: "sm" })}>
          Browse Assets
        </Link>
        <Button variant="outline" size="sm" disabled title="Enabled with Module 1">
          Run Assessment
        </Button>
        <Button variant="outline" size="sm" disabled title="Enabled with Module 3">
          Build Kit
        </Button>
      </CardContent>
    </Card>
  );
}

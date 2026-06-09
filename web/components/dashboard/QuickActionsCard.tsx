import Link from "next/link";

import { Button, buttonVariants } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

// Browse Assets (Module 2) and Run Assessment (Module 1) are live. Build Kit is
// disabled until Module 3 lands.
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
        <Link
          href="/modules/maturity-assessment"
          className={buttonVariants({ variant: "outline", size: "sm" })}
        >
          Run Assessment
        </Link>
        <Button variant="outline" size="sm" disabled title="Enabled with Module 3">
          Build Kit
        </Button>
      </CardContent>
    </Card>
  );
}

import Link from "next/link";

import { buttonVariants } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

// Browse Assets (Module 2), Run Assessment (Module 1), and Build Kit (Module 3)
// are all live.
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
        <Link
          href="/modules/kit-builder"
          className={buttonVariants({ variant: "outline", size: "sm" })}
        >
          Build Kit
        </Link>
      </CardContent>
    </Card>
  );
}

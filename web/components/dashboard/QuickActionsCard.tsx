import Link from "next/link";

import { buttonVariants } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

// Browse Assets (Module 2), Run Assessment (Module 1), Build Kit (Module 3),
// Governance Check (Module 4), and Ethics Review (Module 21) are all live.
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
        <Link
          href="/modules/governance"
          className={buttonVariants({ variant: "outline", size: "sm" })}
        >
          Governance Check
        </Link>
        <Link
          href="/modules/ethics-checker"
          className={buttonVariants({ variant: "outline", size: "sm" })}
        >
          Ethics Review
        </Link>
        <Link
          href="/modules/exchange"
          className={buttonVariants({ variant: "outline", size: "sm" })}
        >
          Skills Exchange
        </Link>
        <Link
          href="/modules/roi-calculator"
          className={buttonVariants({ variant: "outline", size: "sm" })}
        >
          ROI Calculator
        </Link>
      </CardContent>
    </Card>
  );
}

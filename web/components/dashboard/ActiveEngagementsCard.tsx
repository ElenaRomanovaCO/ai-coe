import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

// Wave 1 placeholder — live data arrives with Module 18 (Wave 5).
export function ActiveEngagementsCard() {
  return (
    <Card className="h-full" title="Coming soon — enabled with Module 18">
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          Active Engagements
          <span className="rounded bg-neutral-100 px-1.5 py-0.5 text-[10px] font-normal uppercase text-neutral-500">
            Soon
          </span>
        </CardTitle>
      </CardHeader>
      <CardContent>
        <p className="text-sm text-neutral-400">
          No active engagements. Start one when the Project Health module is enabled.
        </p>
      </CardContent>
    </Card>
  );
}

import { STAGE_NAMES } from "@/lib/assessment";
import { cn } from "@/lib/utils";

// Reusable 0-5 maturity stage indicator (design-system motif): a 6-segment bar.
// Used on the assessment result, and reusable on the dashboard / asset cards.
export function StageIndicator({
  stage,
  size = "md",
  showLabel = true,
}: {
  stage: number;
  size?: "sm" | "md";
  showLabel?: boolean;
}) {
  const seg = size === "sm" ? "h-1.5" : "h-2.5";
  return (
    <div>
      <div className="flex gap-1" role="img" aria-label={`Stage ${stage} of 5`}>
        {[0, 1, 2, 3, 4, 5].map((i) => (
          <div
            key={i}
            className={cn(
              "flex-1 rounded-full transition-colors",
              seg,
              i <= stage ? "bg-indigo-600" : "bg-slate-200",
            )}
          />
        ))}
      </div>
      {showLabel && (
        <p className="mt-2 text-sm font-medium text-slate-700">
          Stage {stage} of 5 — {STAGE_NAMES[stage] ?? "Unknown"}
        </p>
      )}
    </div>
  );
}

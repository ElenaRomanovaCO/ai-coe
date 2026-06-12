"use client";

// Lightweight, opt-in guided tour overlay (FR-068). Given a `tourId` + ordered
// `steps`, it shows a centered walkthrough modal the first time a user opens the
// page (tracked per-tour in localStorage), with Back / Next / Skip. It never
// re-shows once dismissed; a "Take a tour" button can re-trigger it via the
// exported `startTour` event. No external deps — built on our button styles.

import { useCallback, useEffect, useState } from "react";
import { ArrowLeft, ArrowRight, Compass, X } from "lucide-react";

import { Button } from "@/components/ui/button";

export interface TourStep {
  title: string;
  body: string;
}

const SEEN_PREFIX = "tour_seen_";

function tourEventName(tourId: string): string {
  return `aicoe:start-tour:${tourId}`;
}

/** Fire from anywhere (e.g. a "Take a tour" button) to (re)open a tour. */
export function startTour(tourId: string): void {
  if (typeof window !== "undefined") {
    window.dispatchEvent(new CustomEvent(tourEventName(tourId)));
  }
}

export function GuidedTour({
  tourId,
  steps,
  autoStart = true,
}: {
  tourId: string;
  steps: TourStep[];
  autoStart?: boolean;
}) {
  const [open, setOpen] = useState(false);
  const [step, setStep] = useState(0);

  const seenKey = `${SEEN_PREFIX}${tourId}`;

  const markSeen = useCallback(() => {
    try {
      window.localStorage.setItem(seenKey, "1");
    } catch {
      // localStorage may be unavailable; the tour simply won't persist dismissal.
    }
  }, [seenKey]);

  // Auto-open once per user (per browser) on first visit. Deferred to a timeout
  // so we never call setState synchronously in the effect body (React-19 rule).
  useEffect(() => {
    if (!autoStart) return;
    let seen = "1";
    try {
      seen = window.localStorage.getItem(seenKey) ?? "";
    } catch {
      seen = "1";
    }
    if (seen) return;
    const id = setTimeout(() => {
      setStep(0);
      setOpen(true);
    }, 0);
    return () => clearTimeout(id);
  }, [autoStart, seenKey]);

  // Allow manual re-trigger.
  useEffect(() => {
    function onStart() {
      setStep(0);
      setOpen(true);
    }
    const name = tourEventName(tourId);
    window.addEventListener(name, onStart);
    return () => window.removeEventListener(name, onStart);
  }, [tourId]);

  // Esc closes (and marks seen).
  useEffect(() => {
    if (!open) return;
    function onKey(e: KeyboardEvent) {
      if (e.key === "Escape") close();
    }
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [open]);

  function close() {
    markSeen();
    setOpen(false);
  }

  if (!open || steps.length === 0) return null;
  const current = steps[Math.min(step, steps.length - 1)];
  const isLast = step >= steps.length - 1;

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4"
      role="dialog"
      aria-modal="true"
      aria-label="Guided tour"
      onClick={close}
    >
      <div
        className="w-full max-w-md rounded-xl border border-neutral-200 bg-white p-6 shadow-xl"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="mb-3 flex items-start justify-between gap-3">
          <div className="flex items-center gap-2">
            <span className="flex h-8 w-8 items-center justify-center rounded-full bg-indigo-100 text-indigo-600">
              <Compass className="h-4 w-4" />
            </span>
            <h2 className="text-base font-semibold text-neutral-900">{current.title}</h2>
          </div>
          <button
            onClick={close}
            aria-label="Skip tour"
            className="rounded p-1 text-neutral-400 hover:bg-neutral-100 hover:text-neutral-700"
          >
            <X className="h-4 w-4" />
          </button>
        </div>

        <p className="text-sm leading-relaxed text-neutral-600">{current.body}</p>

        <div className="mt-5 flex items-center justify-between">
          <div className="flex gap-1.5">
            {steps.map((_, i) => (
              <span
                key={i}
                className={`h-1.5 w-1.5 rounded-full ${
                  i === step ? "bg-indigo-600" : "bg-neutral-300"
                }`}
              />
            ))}
          </div>
          <div className="flex items-center gap-2">
            {step > 0 && (
              <Button variant="ghost" size="sm" onClick={() => setStep((s) => s - 1)}>
                <ArrowLeft className="h-4 w-4" /> Back
              </Button>
            )}
            {isLast ? (
              <Button size="sm" onClick={close}>
                Done
              </Button>
            ) : (
              <Button size="sm" onClick={() => setStep((s) => s + 1)}>
                Next <ArrowRight className="h-4 w-4" />
              </Button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

# Page Brief — AI Maturity Assessment

> Inherits `../design-system.md`. Route: `/modules/maturity-assessment`. Module 1
> (AGENT-02), Wave 2. Covers FR-016..019.

## Purpose

Run a guided assessment of an organization's AI maturity (stages 0–5) and produce a
staged result with recommendations. One of the demo's centerpieces — it should feel like
a smart, structured interview, not a dumb form.

## Who & when

A consultant assessing a client (often live in a workshop, sometimes async). Wants to
move quickly through questions and land on a credible stage + next steps.

## Content & data

- **Intake:** a few framing inputs (client industry, size band, focus area) — generic,
  no names.
- **Questionnaire:** questions grouped by dimension (Strategy & sponsorship, Data
  readiness, Talent & skills, Governance & risk, Technology & tooling). Each dimension
  scored 0–5. Can be answered conversationally (via the dock) or via this guided UI.
- **Result:** an overall **stage (0–5)** with the reusable stage indicator, per-dimension
  scores (radar or bar), the **binding constraint**, and **recommended next steps**.
- Tie-ins: recommended assets/kits for the stage; "generate client report" (Module 14).

## Primary actions

Start/resume an assessment · answer questions (with progress) · review/edit scores ·
view result · save · export/report · jump to recommended assets.

## States

- **Intro/empty** — explain the 5 dimensions, "start assessment".
- **In progress** — one dimension at a time, progress bar, back/next, save-and-resume.
- **Result** — the scored summary (hero), per-dimension breakdown, recommendations.
- **Loading / error** — skeletons; calm error.

## Layout

Stepper or progress rail on the left; current dimension's questions in the main column.
Result view = a hero stage card + a radar/bar chart of dimensions + a recommendations
panel + recommended-assets row.

## Design prompt seed

> Design an "AI Maturity Assessment" flow for an enterprise AI-consulting platform. Two
> screens: (1) the in-progress questionnaire — a left progress rail listing five
> dimensions (Strategy & Sponsorship, Data Readiness, Talent & Skills, Governance & Risk,
> Technology & Tooling), the current dimension's 0–5 scaled questions in the main column,
> with a progress bar and back/next + "save & resume"; (2) the results screen — a hero
> card showing the overall maturity stage on a 0–5 indicator ("Stage 2 — Piloting"), a
> radar/bar chart of the five dimension scores, a "binding constraint" callout, a
> "recommended next steps" list, and a row of recommended asset cards, plus a "Generate
> client report" button. Credible, structured, calm enterprise look; indigo accent; Inter;
> rounded-lg; light + dark. Use a generic "regional bank, Stage 2" example — no company
> names.

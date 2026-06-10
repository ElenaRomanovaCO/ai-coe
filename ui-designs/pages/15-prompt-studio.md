# Page Brief — Prompt Engineering Studio

> Inherits `../design-system.md`. Route: `/modules/prompt-studio`. Module 11 (AGENT-11),
> Wave 4. Covers FR-036..038.

## Purpose

Browse, fork, version, and refine reusable prompt templates. A small "prompt library +
editor + diff" for consulting prompts.

## Content & data (real prompt fields)

Prompt entries: `title`, `use_case`, `model_targets[]`, `variables[]`, `version`,
`parent_id` (forks). Body = the prompt text with `{{variables}}`. (Seed: kickoff
facilitation, use-case prioritization, exec briefing, risk assessment, retro extraction.)

## Primary actions

- Browse/search prompts; filter by use case.
- Open a prompt → view text, variables, model targets, version.
- **Fork** → edit a copy (new version), with a **diff vs parent**.
- Try/run a prompt (fill variables) — optional.

## States

Library (list) · editor (prompt text + variables) · diff (fork vs parent) · empty.

## Layout

Left: prompt library list. Main: the prompt editor (text area with variable chips,
model-target tags, version info). Diff view = side-by-side or inline highlight vs parent.

## Design prompt seed

> Design a "Prompt Engineering Studio" page for an enterprise AI-consulting platform. Left
> sidebar: a searchable list of prompt templates (e.g. "Client Kickoff Facilitation",
> "Use Case Prioritization", "Executive Briefing"). Main: a prompt editor showing the
> prompt text with highlighted `{{variables}}`, a row of variable chips, model-target
> tags, and version info, plus "Fork" and "Save new version" actions. Also show a diff
> view comparing a forked prompt against its parent (side-by-side with added/removed
> highlighting) and an optional "try it" panel to fill variables. Developer-tool-meets-
> docs aesthetic, clean, monospace for prompt text, indigo accent; Inter for UI; rounded-
> lg; light + dark. No company names.

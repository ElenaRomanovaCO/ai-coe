# Page Brief — Engagement Retrospective Tracker

> Inherits `../design-system.md`. Route: `/modules/retrospective`. Module 16 (AGENT-15),
> Wave 5. Covers FR-054..055.

## Purpose

Capture engagement retrospectives and extract reusable insights (what worked, what didn't,
reusable assets, action items). Feeds the Knowledge Contribution module.

## Content & data

- **Retro entries:** per engagement — what worked, what didn't (root causes), reusable
  assets identified, action items (owned, dated).
- **Insight extraction:** AI-generated, generalized lessons from raw notes.

## Primary actions

Create a retro (paste notes → extract) · review/edit extracted insights · promote a
reusable asset to Contribution · assign action items · browse past retros.

## States

Retro list · new-retro (notes → extracted insights) · detail · empty.

## Layout

Input: paste raw retro notes. Output: four sections — What worked / What didn't /
Reusable assets / Action items — each editable. A list of past retros for browse.

## Design prompt seed

> Design an "Engagement Retrospective Tracker" page for an enterprise AI-consulting
> platform. A two-step surface: (1) an input where a consultant pastes raw retro notes and
> clicks "Extract insights"; (2) a structured output with four editable sections — "What
> worked" (reusable guidance), "What didn't" (root causes), "Reusable assets" (each with a
> suggested title + content type and a "promote to library" button), and "Action items"
> (owned, dated, checkable). Plus a list of past retrospectives to browse. Reflective,
> organized, calm; indigo accent; Inter; rounded-lg; light + dark. Generic engagement
> examples, no company names.

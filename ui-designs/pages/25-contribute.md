# Page Brief — Knowledge Contribution

> Inherits `../design-system.md`. Route: `/modules/contribute`. Module 5 (AGENT-06),
> Wave 6. Covers FR-064..066.

## Purpose

Capture, structure, and submit a new knowledge asset to the vault — turn a consultant's
notes/pattern into a schema-valid, reusable asset. Includes a light curation/review step.

## Content & data

- **Draft editor:** title + markdown body + structured frontmatter fields (type, industry,
  ai_stage, tags) with validation against the asset schema.
- **AI assist:** help structuring raw notes into the schema; suggest tags/type.
- **Review/curation:** a submission status (draft → submitted → published) + reviewer notes.

## Primary actions

Start from notes → structure with AI · fill/validate frontmatter · preview · submit ·
track status.

## States

Editor (draft) · validation errors (inline) · preview · submitted · empty.

## Layout

Split: left = the markdown/body editor; right = the frontmatter form (validated) + a
"structure with AI" helper. A preview toggle shows the finished asset.

## Design prompt seed

> Design a "Knowledge Contribution" page for an enterprise AI-consulting platform where a
> consultant turns notes into a reusable, schema-valid asset. Split layout: left, a
> markdown body editor; right, a structured frontmatter form (Title, Type [reference-
> architecture / solution-pattern / …], Industry, AI maturity stage, Tags) with inline
> validation, plus a "Structure my notes with AI" helper that fills fields and suggests
> tags. Include a preview toggle that renders the finished asset, a submission-status
> indicator (Draft → Submitted → Published), and a submit button. Clean authoring-tool
> aesthetic; indigo accent; Inter for UI, monospace where editing; rounded-lg; light +
> dark. Generic example content — no company names.

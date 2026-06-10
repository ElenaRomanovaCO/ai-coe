# Page Brief — Engagement Kit Builder

> Inherits `../design-system.md`. Route: `/modules/kit-builder`. Module 3 (AGENT-04),
> Wave 2. Covers FR-020..022.

## Purpose

Assemble a tailored "engagement kit" — a curated bundle of assets, templates, and
checklists for a specific client context — and export it. Turns scattered assets into a
ready-to-use package.

## Who & when

A consultant preparing for an engagement/kickoff who wants a coherent set of deliverables
in one place, fast.

## Content & data

- **Context inputs:** industry, engagement type, AI stage (drives suggestions).
- **Suggested assets:** ranked asset cards the agent recommends for the context (reuse the
  AssetCard); add/remove to the kit.
- **Kit canvas:** the current kit — an ordered list of included assets (title, type,
  reorder, remove), a kit title/description, and a count.
- **Export:** download as a bundle (zip) / shareable view.

## Primary actions

Set context · accept/add/remove suggested assets · reorder · name the kit · save · export
(zip) · open an included asset.

## States

- **Empty** — "describe the engagement to start", with the context inputs.
- **Building** — suggestions on one side, the kit canvas on the other.
- **Ready** — kit named + populated, export enabled.
- **Loading / error.**

## Layout

Two-pane: left = context + ranked **suggestions**; right = the **kit canvas** (drag-to-
reorder list) with title/description and export. On mobile, stack with tabs (Suggestions /
Your Kit).

## Design prompt seed

> Design an "Engagement Kit Builder" page for an enterprise AI-consulting platform. A
> two-pane layout: left pane has context inputs (industry, engagement type, AI maturity
> stage) and a ranked list of suggested asset cards (title, content-type badge, industry,
> stage) each with an "Add to kit" button; right pane is the "kit canvas" — an editable,
> drag-to-reorder list of included assets with remove buttons, an editable kit title and
> description, an item count, and a primary "Export kit (.zip)" button. Show an empty
> state ("Describe the engagement to get suggestions") and a populated, ready-to-export
> state. Practical, organized, indigo accent, Inter, rounded-lg cards, light + dark. Use a
> generic "fintech fraud-scoring engagement" example — no company names.

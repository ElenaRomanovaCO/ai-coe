# Page Brief — Asset Detail

> Inherits `../design-system.md`. Route: `/modules/asset-library/[id]`. Module 2.
> Covers FR-011..013. Chat citations deep-link here.

## Purpose

Read one asset in full, see its metadata, and act on it (save, rate, flag, chat with
it). The destination for both browsing and chat citations.

## Who & when

A consultant who clicked an asset (from the library or a chat citation) and wants to
read it, judge its fit, and reuse it.

## Content & data

- **Header:** asset `title`, content-type badge, `industry`, **AI-stage indicator**,
  `tags[]`, `updated_at`, `contributor`. A "back to library" link.
- **Body:** the asset's markdown rendered cleanly (headings, lists, tables, code) — this
  is the main reading surface. Comfortable measure (~65–75ch), strong type hierarchy.
- **Frontmatter / metadata panel:** a side panel summarizing the structured fields
  (id, type, industry, stage, use_case_type, tags) in a tidy key–value list.
- **Actions:** Save/pin, Rate (e.g. thumbs or stars), Flag (report an issue) — these
  persist as sidecars; reflect optimistic state.
- **"Chat with this asset"** entry point (Module 26 later) — a button that opens the dock
  scoped to this document.
- **Related assets:** a few semantically-related assets (cards) at the bottom.

## Primary actions

Read · Save · Rate · Flag · Chat-with-this · navigate to a related asset · back to library.

## States

- **Loading** — skeleton (header + body lines + panel).
- **Populated** — full render.
- **Not found** — clean 404 ("this asset doesn't exist or isn't available") with a link
  back to the library. (Important: chat citations may point here before/if an asset is
  missing.)
- **Action feedback** — saved/rated/flagged confirmations (subtle toast or state change).

## Layout

Two-column on desktop: wide **reading column** (markdown body) + a narrower right
**metadata/actions panel** (sticky). Single column on mobile (panel collapses above or
into a sheet). Related assets as a row of cards beneath the body.

## Components

MarkdownRenderer (typographic prose), FrontmatterPanel (key–value), Badge, stage
indicator, Button group (save/rate/flag/chat), Card (related), Skeleton, Toast.

## Visual direction

A focused reading experience — document-first, generous whitespace, quiet chrome. The
metadata panel is reference, not decoration. Make markdown gorgeous (this is where the
KB content lives).

## Design prompt seed

> Design an asset detail page for an enterprise AI-consulting knowledge platform. Two
> columns on desktop: a wide reading column rendering a markdown document (title,
> headings, body, a table, a bulleted checklist) with beautiful typography at a
> comfortable measure; and a narrower sticky right panel showing structured metadata as a
> key–value list (id, type, industry, AI maturity stage with a 0–5 indicator,
> use-case tags, last updated, contributor) plus an action group: Save, Rate (thumbs),
> Flag, and a primary "Chat with this asset" button. A content-type badge and "back to
> library" link in the header; a row of "related assets" cards at the bottom. Show the
> populated state and a clean "asset not found" state. Document-first, calm, indigo
> accent, Inter for UI + readable serif or sans for prose, rounded-lg, light + dark.
> Use a generic healthcare "Clinical Notes RAG reference architecture" as the sample —
> no company names.

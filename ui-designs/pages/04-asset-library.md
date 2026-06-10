# Page Brief — Asset Library (Browse)

> Inherits `../design-system.md`. Route: `/modules/asset-library`. Module 2 (AGENT-03).
> Covers FR-010..013.

## Purpose

Browse, filter, and search the knowledge base of reusable assets (reference
architectures, solution patterns, templates, checklists, …). The consultant's "shelf of
proven starting points."

## Who & when

A consultant scoping or delivering an engagement, looking for a relevant artifact by
industry, maturity stage, type, or free-text intent.

## Content & data (real asset fields)

Each asset card shows: `title`, a **content/type badge** (`reference-architecture`,
`solution-pattern`, `kickoff-template`, `discovery-questionnaire`, `workshop-agenda`,
`roi-template`, `risk-checklist`), `industry`, an **AI-stage indicator** (`ai_stage`
0–5), `tags[]` (truncated), and `updated_at`. Optionally a save/pin control.

## Primary actions

- **Search** — a prominent search bar (semantic search over the vault; returns ranked
  assets). Results can show a relevance hint.
- **Filter** — by `industry`, `type`, `ai_stage`, `tags`. Multi-select; show active
  filters as removable chips; a clear-all.
- **Open** an asset → asset detail page.
- **Save / pin** an asset (optimistic toggle).

## States

- **Default browse** — all assets in a grid, filters available.
- **Searching / filtered** — ranked or filtered subset; show count + active filters.
- **No results** — friendly empty state with a "clear filters" / "try a broader search"
  nudge.
- **Loading** — skeleton cards.

## Layout

Header row: page title + search bar + result count. Left (or top) **filter rail**
(industry, type, stage, tags). Main: responsive **card grid** (3–4 cols desktop, 1 mobile).
Card is the workhorse — keep it scannable, consistent height. Sort control (relevance /
recently updated).

## Components

Search Input, filter controls (checkbox groups / DropdownMenu / chips), Card (AssetCard),
content-type Badge, the **stage indicator**, Skeleton, Pagination or infinite scroll.

## Visual direction

Clean, library-like, scannable. Let the content-type accent colors + icons do the
visual sorting. Dense but breathable; cards align to a tidy grid.

## Notes for implementation

- Cards link to `/modules/asset-library/{id}`.
- Chat citations deep-link to the same detail route, so the card → detail mapping must
  match the citation's `asset_library_url`.

## Design prompt seed

> Design an "Asset Library" browse page for an enterprise AI-consulting platform. Top: a
> page title, a prominent semantic search bar, and a result count. A left filter rail
> with multi-select groups for Industry, Type, AI maturity stage (0–5), and Tags, with
> active filters shown as removable chips. Main area: a responsive grid of asset cards —
> each card shows the title, a colored content-type badge (e.g. "Reference Architecture",
> "Solution Pattern", "Risk Checklist"), the industry, a compact 0–5 AI-stage indicator,
> a couple of tags, and a "last updated" date, plus a save/pin icon. Include a sort
> control (relevance / recently updated). Show three states: populated grid, a filtered/
> searching state, and a no-results empty state. Clean library aesthetic, indigo accent,
> muted per-type colors + lucide icons, Inter, rounded-lg cards, light + dark. Generic
> demo assets across healthcare, financial services, retail, manufacturing — no company
> names.

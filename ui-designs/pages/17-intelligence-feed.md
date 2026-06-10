# Page Brief — AI Intelligence Feed & Release Radar

> Inherits `../design-system.md`. Route: `/modules/intelligence-feed`. Modules 24 + 15
> (AGENT-23), Wave 5. Covers FR-042..044.

## Purpose

A personalized feed of AI developments with CoE "what this means" commentary, plus a
**radar** view (adopt/trial/assess/hold). The "stay current" surface.

## Content & data (real feed fields)

Feed items: `title`, `category` (model-release / tool-launch / research / vendor-update /
industry-news), `published_at`, `industries[]`, `tags[]`, `radar_status` (adopt / trial /
assess / hold | none), and a "what this means" commentary block.

## Primary actions

Scroll the feed · filter by category/industry/radar status · toggle **feed vs radar**
view · open an item · save/share.

## States

Feed (cards, newest first) · radar (quadrant/ring) · filtered · empty · loading.

## Layout

Two views via tabs: **Feed** = a chronological list/cards (title, category badge, date,
"what this means" snippet, radar chip); **Radar** = a tech-radar style ring/quadrant
plotting items by `radar_status`. Filters across both.

## Design prompt seed

> Design an "AI Intelligence Feed & Release Radar" page for an enterprise AI-consulting
> platform with two tabbed views. Feed view: a chronological list of cards — each shows a
> title, a category badge (model-release / tool-launch / research / vendor-update), a date,
> a short "What this means" CoE commentary snippet, and an adopt/trial/assess/hold radar
> chip; with filters for category, industry, and radar status. Radar view: a tech-radar
> style ring chart with four rings (Adopt, Trial, Assess, Hold) plotting the items as dots
> grouped by category quadrant. Current, editorial-but-clean, indigo accent + status
> colors; Inter; rounded-lg; light + dark. Generic AI-industry items — no company names.

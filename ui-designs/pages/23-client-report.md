# Page Brief — Client-Facing Maturity Report Portal

> Inherits `../design-system.md`. Route: `/modules/client-report`. Module 14 (AGENT-14),
> Wave 6. Covers FR-058..060.

## Purpose

Generate a polished, **client-ready** maturity report (PDF) from an assessment — the one
surface a consultant shows the client, so it must look the most refined.

## Content & data

- **Source:** an assessment (stage, dimension scores, recommendations).
- **Report:** a branded document — exec summary, maturity stage visual, dimension
  breakdown, recommendations/roadmap, benchmarks (optional).
- **Preview + export:** WYSIWYG preview → download PDF / share link.

## Primary actions

Pick an assessment → generate report · edit sections/copy · preview · export PDF · share.

## States

Empty (pick assessment) · generating · preview (editable) · exported.

## Layout

Two-pane: left = section editor/outline; right = a live **report preview** (paginated,
client-grade). Export bar on top.

## Design prompt seed

> Design a "Client Maturity Report" generator for an enterprise AI-consulting platform —
> the most polished, client-presentable surface. Two-pane: left, an outline/section editor
> (Executive Summary, Maturity Stage, Dimension Breakdown, Recommendations & Roadmap,
> Benchmarks) with editable copy; right, a live paginated report preview that looks like a
> beautifully designed PDF — a cover with the maturity stage as a hero visual, a dimension
> breakdown chart, a recommendations roadmap, all in a refined, neutral, white-label
> document style. Top: a "Generate from assessment" selector and an "Export PDF" /
> "Share" bar. Elegant, executive-grade, restrained; subtle indigo accent; refined
> typography; light primary. White-label (no company names) — generic client example.

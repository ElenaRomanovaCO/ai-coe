# Page Brief — Universal Asset Q&A ("Chat with Anything")

> Inherits `../design-system.md`. Route: `/modules/asset-qa` (also invoked from an asset's
> "Chat with this asset"). Module 26 (AGENT-25), Wave 2. Covers FR-023..024.

## Purpose

Focused Q&A scoped to a **single document/asset** — summarize it, interrogate it, pull
specifics — distinct from the global Copilot dock (which searches the whole KB). The
"chat with this PDF/doc" experience, on vault assets.

## Who & when

A consultant reading or evaluating one asset who wants to ask questions about *that file*
without wading through it.

## Content & data

- **Document pane:** the selected asset rendered (markdown) with its title + content-type
  badge — the thing being questioned.
- **Q&A pane:** a scoped chat — user questions and streamed, cited answers where citations
  point to **sections within this document** (heading anchors), not the whole KB.
- **Suggested questions:** 3–4 starters derived from the doc ("Summarize this",
  "What are the key risks?", "What stage is this for?").
- A picker to choose which asset to chat with (if entered without one).

## Primary actions

Pick an asset · ask a scoped question · click a citation → scroll to that section · clear/
new question · open the full asset.

## States

- **No asset selected** — a picker / recent assets.
- **Active** — split doc + chat, suggested questions on first load.
- **Streaming / error** — same patterns as the dock.

## Layout

Split view: left = **document** (scrollable), right = **scoped chat** (transcript +
composer). On mobile, tabs (Document / Ask) or chat over a collapsible doc.

## Design prompt seed

> Design a "Chat with this asset" / universal asset Q&A page for an enterprise
> AI-consulting platform. A split view: left pane renders a single markdown document (a
> generic healthcare "Clinical Notes RAG reference architecture") with its title and a
> content-type badge; right pane is a focused chat scoped to THAT document — show a couple
> of suggested starter questions ("Summarize this", "What are the key risks?"), a user
> question, and a streamed answer whose citation chips reference sections *within the
> document* (e.g. "§ Controls") and scroll-to on click. Include the composer with send/
> stop. Distinguish it visually from a global search chat (it's about one doc). Calm,
> focused, indigo accent, Inter, rounded-lg, light + dark. No company names.

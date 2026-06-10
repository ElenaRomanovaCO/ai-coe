# Page Brief — Claude Code Development Accelerator

> Inherits `../design-system.md`. Route: `/modules/code-accelerator`. Module 27
> (AGENT-26, Opus, cost-capped), Wave 7. Covers FR-074..077.

## Purpose

Generate a scaffolded starter codebase from a reference architecture — pick an
architecture, generate runnable boilerplate, download a zip. The most "developer" surface.

## Content & data

- **Source:** a reference-architecture asset to scaffold from.
- **Options:** target stack/runtime, project name.
- **Generation:** streamed progress (files being created), a file tree preview, code
  viewer.
- **Cost guard:** the daily **Opus cap** is visible — show remaining budget / a cap-hit
  state (this is the only Opus module).
- **Output:** a downloadable zip + a README referencing the source architecture.

## Primary actions

Pick architecture + options → generate · watch progress · browse generated files · download
zip · regenerate.

## States

Setup (pick arch + options) · generating (streamed file tree + progress) · ready (file tree
+ code viewer + download) · **cap-exceeded** (friendly "daily Opus budget reached") · error.

## Layout

Setup form → a generation view with a **file-tree sidebar** + a code viewer (syntax
highlighted) + a progress/log strip; a download bar. A small budget indicator in the header.

## Design prompt seed

> Design a "Code Development Accelerator" page for an enterprise AI-consulting platform
> that scaffolds a starter codebase from a reference architecture. Setup state: pick a
> source reference architecture (e.g. "Healthcare Clinical Notes RAG"), a target stack
> (Python + FastAPI + AWS Lambda), and a project name. Generating state: a streamed view
> with a file-tree sidebar populating in real time, a syntax-highlighted code viewer, and
> a progress/log strip. Ready state: the full generated file tree, a code viewer, and a
> "Download .zip" button, plus a README preview that references the source architecture.
> Include a small daily-budget indicator in the header (this module uses a cost-capped
> premium model) and a friendly "daily budget reached" state. Developer-IDE aesthetic
> (think a clean code editor), monospace code, indigo accent; Inter for UI; dark mode
> especially polished. No company names.

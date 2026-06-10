# Page Brief — Decision Log

> Inherits `../design-system.md`. Route: `/modules/decision-log`. Module 19 (AGENT-18),
> Wave 5. Covers FR-048..050.

## Purpose

Record architecture/engagement decisions with rationale, and surface relevant precedent.
A lightweight ADR (architecture decision record) library with similarity search.

## Content & data (decision shape)

Decisions: `title`, the decision, context, options-considered (with verdicts),
consequences, `updated_at`, owner. (Mirrors `vault/decisions/`.)

## Primary actions

Log a new decision (structured form) · browse/search decisions · open one (detail) ·
**find precedent** (similar past decisions) · link a decision to a use case/project.

## States

Log list (timeline/cards) · new-decision form · detail · precedent results · empty.

## Layout

List/timeline of decisions (title, date, a snippet, tags). Detail = the ADR rendered
(Decision / Context / Options table / Consequences). A "similar decisions" panel on detail.

## Design prompt seed

> Design a "Decision Log" page for an enterprise AI-consulting platform — an architecture-
> decision-record library. Main: a timeline/list of decisions, each card showing a title
> (e.g. "Default vector store for internal tools"), a date, a one-line summary, and tags.
> A detail view renders one decision as a structured record: a "Decision" statement, a
> "Context" section, an "Options considered" comparison table with verdicts, and a
> "Consequences" list — plus a "similar past decisions" panel surfacing precedent. Include
> a "Log a decision" structured form. Clean, documentation-grade, calm; indigo accent;
> Inter for UI, monospace for any IDs; rounded-lg; light + dark. No company names.

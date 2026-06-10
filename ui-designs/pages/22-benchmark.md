# Page Brief — Client Benchmark Comparator

> Inherits `../design-system.md`. Route: `/modules/benchmark`. Module 22 (AGENT-21),
> Wave 5. Covers FR-056..057.

## Purpose

Compare a client's maturity and metrics against peer/industry benchmarks, with charts and
export. "How do we stack up?"

## Content & data

- **Subject:** the client's stage + dimension scores (from an assessment).
- **Benchmarks:** peer/industry averages per dimension (seeded).
- **Comparison:** client vs peer on a radar/bar; percentile/position; gaps highlighted.

## Primary actions

Pick a client/assessment + peer group → compare · toggle dimensions · view gaps · export
(image/PDF) for client use.

## States

Empty (pick inputs) · comparison (charts) · loading · error.

## Layout

Top: subject + peer-group selectors. Main: a radar or grouped-bar chart (client vs peer
average per dimension), a "position vs peers" callout, and a gaps list. Export prominent.

## Design prompt seed

> Design a "Client Benchmark Comparator" page for an enterprise AI-consulting platform.
> Top: selectors for the client/assessment and a peer group (industry + size band). Main:
> a comparison chart — a radar (or grouped bar) overlaying the client's AI-maturity
> dimension scores against peer-industry averages, with gaps highlighted; a "position vs
> peers" callout (e.g. "Above average on Tooling, below on Governance"); and a list of the
> biggest gaps with suggested focus areas. A prominent "Export for client (PDF)" button.
> Polished, client-presentable, calm; indigo accent + a clear two-series chart palette;
> Inter; rounded-lg; light + dark. Generic "regional bank vs peers" example — no company
> names.

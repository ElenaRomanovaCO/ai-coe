# Page Brief — AI Use Case Ideation Engine

> Inherits `../design-system.md`. Route: `/modules/use-case-ideation`. Module 12
> (AGENT-12), Wave 5. Covers FR-045..047.

## Purpose

Generate and rank candidate AI use cases for a client context, on a value-vs-effort grid.
The "where could AI help?" brainstorming + prioritization surface.

## Content & data

- **Input:** client context (industry, goals, constraints, time horizon).
- **Candidates:** generated use cases, each with value (low/expected/high), feasibility,
  a one-line rationale, and the key sensitive assumption.
- **Prioritization:** a value-vs-effort 2×2 grid; ranked top picks; deferred list.

## Primary actions

Describe context → generate · accept/dismiss/edit candidates · view the value/effort grid ·
mark top picks · export shortlist · send a pick to the Decision Log.

## States

Empty (context input) · generating · candidates (list + grid) · refined · error.

## Layout

Context input at top. Results: a ranked candidate list on one side and a value-vs-effort
**2×2 scatter** on the other; a "top 3 / deferred" summary.

## Design prompt seed

> Design an "AI Use Case Ideation" page for an enterprise AI-consulting platform. Top: a
> context input (industry, goals, constraints, time horizon) with a "Generate use cases"
> button. Results: a split layout — left, a ranked list of candidate use cases, each card
> showing the idea, a value rating (low/expected/high), a feasibility rating, a one-line
> rationale, and the key assumption it's sensitive to, with accept/dismiss; right, a
> value-vs-effort 2×2 scatter plotting the candidates (quadrants labeled Quick Wins, Big
> Bets, Fill-ins, Money Pits). Add a "top 3 / deferred" summary and "export shortlist".
> Energetic but structured workshop feel; indigo accent; Inter; rounded-lg; light + dark.
> Use a generic "mid-size retailer" example — no company names.

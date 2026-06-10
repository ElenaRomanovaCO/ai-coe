# Page Brief — Governance & Risk Checker

> Inherits `../design-system.md`. Route: `/modules/governance-checker`. Module 4
> (AGENT-05), Wave 3. Covers FR-025..026.

## Purpose

Run a proposed AI use case through governance and risk controls and surface a structured
list of gaps, severities, and mitigations — a pre-delivery "risk pass."

## Content & data

- **Input:** a use-case description (free text) + context (industry, data sensitivity,
  autonomy level).
- **Findings:** a list of checks, each with a control name, **severity** (low/med/high
  via semantic colors), a finding, and a recommended mitigation.
- **Summary:** overall risk posture + count by severity; "top 3 to fix before pilot."
- Links to relevant regulations (Module 25) and the model-risk checklist asset.

## Primary actions

Submit a use case · review findings (expand each) · mark a finding addressed · export the
report · jump to a cited regulation/asset.

## States

Empty (input prompt) · running (analyzing…) · results (findings table/cards) · error.

## Layout

Top: the use-case input + context. Below: a summary banner (risk posture + severity
counts) and a findings list (cards or a table grouped by severity, highest first).

## Design prompt seed

> Design a "Governance & Risk Checker" results page for an enterprise AI-consulting
> platform. Top: a summary banner showing overall risk posture and counts by severity
> (high/medium/low with red/amber/green). Below: a list of findings grouped by severity
> (highest first) — each finding card shows a control name (e.g. "Explainability",
> "Disparate impact testing", "Human override"), a severity badge, the finding text, and
> a recommended mitigation, with an "addressed" checkbox and a link to a related
> regulation. Include the input area at top (a use-case description + industry/data-
> sensitivity/autonomy selectors) and an "Export report" button. Serious, trustworthy,
> calm; indigo accent + semantic severity colors; Inter; rounded-lg; light + dark. Use a
> generic "credit-scoring model" example — no company names.

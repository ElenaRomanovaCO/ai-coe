# Page Brief — AI Ethics & Bias Checker

> Inherits `../design-system.md`. Route: `/modules/ethics-checker`. Module 21 (AGENT-20),
> Wave 3. Covers FR-027..028.

## Purpose

Review a use case for ethical risks and potential bias across dimensions, and recommend
mitigations. Sibling to the Governance checker, focused on fairness/harms.

## Content & data

- **Input:** use-case description + who it affects + data used.
- **Dimensions:** fairness/bias, transparency, accountability, privacy, potential harms —
  each rated low/med/high with rationale + mitigation.
- **Affected-groups view:** a short list of stakeholder groups and how each could be
  impacted.
- **Summary:** top ethical concerns + whether to keep the use case advisory
  (human-in-the-loop).

## Primary actions

Submit · review per-dimension findings · expand affected-groups · accept mitigations ·
export.

## States

Empty · analyzing · results · error.

## Layout

Input at top; a dimension scorecard (5 dimensions with severity), an "affected groups"
panel, and a recommendations summary.

## Design prompt seed

> Design an "AI Ethics & Bias Checker" results page for an enterprise AI-consulting
> platform. Show a scorecard of ethical dimensions (Fairness & Bias, Transparency,
> Accountability, Privacy, Potential Harms), each with a low/medium/high rating, a short
> rationale, and a recommended mitigation; an "affected groups" panel listing stakeholder
> groups and potential impacts; and a summary callout with the top concerns and a
> recommendation on whether to keep the use case human-in-the-loop. Include the input area
> (use-case description, who it affects, data used). Thoughtful, calm, trustworthy; indigo
> accent + semantic colors; Inter; rounded-lg; light + dark. Use a generic
> "hiring-screening model" example — no company names.

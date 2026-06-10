# Page Brief — Global AI Regulation & Compliance Tracker

> Inherits `../design-system.md`. Route: `/modules/compliance-tracker`. Module 25
> (AGENT-24), Wave 3. Covers FR-029..031.

## Purpose

Look up the AI regulations that apply to a use case by geography and industry, and track
compliance obligations. A searchable/filterable regulation library + an "applies to me?"
lookup.

## Content & data (real regulation fields)

Regulation entries with: `name`, `geo` (eu / us-federal / us-state-ca / uk / global / …),
`industry_scope[]`, `status` (proposed / enacted / in-effect / superseded),
`effective_date`, `risk_tier`, `tags[]`. (Seed set: EU AI Act, HIPAA, NIST AI RMF, SEC,
GDPR, CA SB-1001, FDA AI/ML, FFIEC.)

## Primary actions

- **Lookup:** pick geography + industry (+ use case) → the applicable regulations, ranked.
- **Browse/filter:** the full regulation library by geo, industry, status.
- **Open** a regulation → detail (summary, key obligations, "what this means").
- Export an obligations summary for a client.

## States

Empty (lookup prompt) · results (applicable list) · browse (filtered library) · detail ·
no-match.

## Layout

A lookup bar (geo + industry selectors) up top; results as a list grouped by
applicability/region with status badges and effective dates; a map or region chips
optional. A detail panel/page renders one regulation.

## Design prompt seed

> Design an "AI Regulation & Compliance Tracker" page for an enterprise AI-consulting
> platform. Top: a lookup bar to select geography (EU, US-Federal, US-State, UK, Global)
> and industry (Healthcare, Financial Services, …). Below: a results list of applicable
> regulations — each row shows the name (EU AI Act, HIPAA, NIST AI RMF, GDPR, FDA AI/ML,
> FFIEC, …), a geography chip, an industry-scope tag, a status badge (in-effect / proposed
> / enacted), and an effective date; clicking opens a detail view with a summary, key
> obligations, and a "what this means for engagements" note. Include a browse/filter mode
> for the whole regulation library and an "export obligations" button. Authoritative,
> clean, reference-library feel; indigo accent + status colors; Inter; rounded-lg; light +
> dark. No company names.

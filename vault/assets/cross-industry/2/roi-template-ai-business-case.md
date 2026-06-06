---
id: roi-template-ai-business-case
title: ROI Template — AI Use Case Business Case
type: roi-template
industry: cross-industry
ai_stage: 2
use_case_type: ["roi", "business-case", "prioritization"]
tags: ["roi", "business-case", "value", "prioritization"]
contributor: demo
updated_at: "2026-05-01"
---

# AI Use Case Business Case (ROI Template)

A lightweight model for estimating the value and cost of a candidate AI use case so
a portfolio can be ranked. Keep estimates ranged, not falsely precise.

## Value drivers

- **Labor time saved** — tasks/period × minutes saved × loaded rate.
- **Quality/error reduction** — error rate delta × cost per error.
- **Revenue uplift** — conversion or retention delta × margin.
- **Risk avoidance** — probability × impact of avoided incidents.

## Cost drivers

- Build (discovery, data prep, model/integration work).
- Run (inference, storage, retrieval, monitoring per month).
- Change (training, process redesign, governance overhead).

## Net value

For each driver, record low / expected / high. Compute payback period and a
12-month net. Flag the two assumptions the result is most sensitive to.

## Decision

Plot the use case on a value vs. effort grid. Anything high-effort and uncertain
should start as a thin pilot before committing to scale. Record the decision in the
Decision Log module.

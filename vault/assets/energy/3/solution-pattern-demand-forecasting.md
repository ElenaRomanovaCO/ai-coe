---
id: solution-pattern-demand-forecasting
title: Solution Pattern — Energy Demand Forecasting with Narrative Insights
type: solution-pattern
industry: energy
ai_stage: 3
use_case_type: ["forecasting", "time-series", "narrative-insights"]
tags: ["energy", "forecasting", "time-series", "explainability"]
contributor: demo
updated_at: "2026-05-15"
---

# Energy Demand Forecasting with Narrative Insights

A pattern that wraps a quantitative demand-forecasting model with an LLM layer that
explains forecast shifts to planners. For stage 3 utilities and energy retailers.

## Problem

Forecasting models produce numbers planners must interpret under time pressure,
especially when weather or events drive sudden shifts. The "why" is buried in
features.

## Pattern

- A time-series model produces demand forecasts with feature contributions
  (weather, calendar, recent load).
- An LLM summarizes what changed versus the prior forecast and why, in plain
  language, with the top contributing factors.
- Planners can ask follow-ups ("what if temperatures run 5 degrees higher?") that
  the system answers by re-querying the model, not by guessing.

## Guardrails

- The forecast model is the source of truth; the LLM never invents numbers.
- Every narrative cites the model's feature contributions.
- Scenario answers come from real model runs, clearly labeled as scenarios.

## Measure

Forecast accuracy is owned by the model; measure the LLM layer by planner adoption
and reduction in time spent interpreting forecasts.

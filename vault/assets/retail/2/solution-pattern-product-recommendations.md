---
id: solution-pattern-product-recommendations
title: Solution Pattern — Conversational Product Recommendations
type: solution-pattern
industry: retail
ai_stage: 2
use_case_type: ["recommendations", "personalization", "conversational"]
tags: ["retail", "recommendations", "personalization", "rag"]
contributor: demo
updated_at: "2026-05-03"
---

# Conversational Product Recommendations

A pattern for a shopping assistant that blends catalog retrieval with light
personalization. Fits stage 2 retailers piloting customer-facing AI.

## Problem

Faceted search struggles with vague, natural-language intent ("a warm jacket for a
rainy commute under $120"). Recommendation models exist but aren't conversational.

## Pattern

- Catalog items are embedded with structured metadata (category, price, season,
  attributes) into a vector index.
- The assistant interprets intent, retrieves candidates, and re-ranks with simple
  personalization signals (recent views, stated preferences).
- It explains *why* each item fits and offers one clarifying question when intent
  is ambiguous.

## Guardrails

- Recommendations are constrained to in-stock catalog items only — no invented SKUs.
- Personalization uses session and consented preference data, not sensitive attributes.
- Price and availability are read at response time, never from the embedding.

## Measure

Add-to-cart rate from assistant sessions, clarifying-question rate, and the share of
recommendations that map to real, in-stock SKUs.

---
id: risk-checklist-model-risk
title: Risk Checklist — AI/ML Model Risk for Financial Services
type: risk-checklist
industry: financial-services
ai_stage: 2
use_case_type: ["model-risk", "governance", "validation"]
tags: ["model-risk", "fintech", "governance", "validation", "sr-11-7"]
contributor: demo
updated_at: "2026-05-09"
---

# AI/ML Model Risk Checklist (Financial Services)

A pre-deployment checklist aligned to common model-risk-management expectations.
Use before promoting any scoring or decisioning model to production.

## Data & inputs

- [ ] Training data lineage documented and access-controlled.
- [ ] Sensitive and proxy attributes identified; use justified or excluded.
- [ ] Representativeness and known gaps assessed.

## Model & validation

- [ ] Independent validation of performance on out-of-time samples.
- [ ] Benchmark against a simpler challenger model.
- [ ] Stability and drift monitoring defined with thresholds.

## Explainability & fairness

- [ ] Decisions are explainable to a regulator and to the affected customer.
- [ ] Disparate-impact testing across protected groups completed.
- [ ] Adverse-action reasons can be generated.

## Operations

- [ ] Human override and appeal path defined.
- [ ] Rollback plan and kill switch tested.
- [ ] Audit logging of inputs, scores, and overrides.

## Sign-off

- [ ] Model owner, validator, and risk officer have signed off.

Pair this checklist with the Governance & Risk Checker module for an automated
first pass.

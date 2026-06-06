---
id: sample-assessment-regional-bank
title: Sample Assessment — Regional Bank (Stage 2)
kind: assessment
owner: demo
updated_at: "2026-05-10"
---

# Sample Assessment — Regional Bank

A completed sample maturity assessment for demo continuity. Generic client; no real
data.

## Result

**Overall stage: 2 (Piloting).** The organization has run isolated AI pilots but has
nothing in production and lacks a governance operating model.

## Dimension scores (0-5)

| Dimension | Score | Note |
|---|---|---|
| Strategy & sponsorship | 3 | Exec sponsor exists; outcomes loosely defined |
| Data readiness | 2 | Data siloed; quality monitoring ad hoc |
| Talent & skills | 2 | Small data team; limited MLOps |
| Governance & risk | 1 | No AI governance committee yet |
| Technology & tooling | 3 | Cloud-native; some ML tooling in place |

## Binding constraint

Governance is the limiting factor. Pilots can't reach production without a risk and
oversight model.

## Recommended next steps

1. Stand up a lightweight AI governance committee (NIST AI RMF as the backbone).
2. Pick one pilot (fraud-scoring rationale assistant) and harden it to production with
   the Model Risk Checklist.
3. Define a quality eval set before scaling.

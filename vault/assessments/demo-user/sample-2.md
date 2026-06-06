---
id: sample-assessment-health-system
title: Sample Assessment — Health System (Stage 1)
kind: assessment
owner: demo
updated_at: "2026-05-24"
---

# Sample Assessment — Health System

A completed sample maturity assessment for demo continuity. Generic client; no real
data.

## Result

**Overall stage: 1 (Exploring).** Strong interest and a clear clinical pain point, but
data access and compliance groundwork are immature.

## Dimension scores (0-5)

| Dimension | Score | Note |
|---|---|---|
| Strategy & sponsorship | 3 | Clinical sponsor; outcome is clinician time saved |
| Data readiness | 1 | PHI siloed; de-identification tooling absent |
| Talent & skills | 1 | No in-house data science |
| Governance & risk | 2 | Privacy office engaged; no AI-specific policy |
| Technology & tooling | 2 | Cloud migration underway |

## Binding constraint

Data readiness and PHI handling. Nothing can proceed until de-identification and a BAA
path exist.

## Recommended next steps

1. Establish de-identification before any embedding; confirm BAAs for model endpoints.
2. Scope a clinical-notes RAG assistant as advisory (human-in-the-loop) to stay outside
   device regulation.
3. Run the Responsible AI Foundations workshop with clinical staff.

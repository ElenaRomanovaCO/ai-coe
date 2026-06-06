---
id: ref-arch-predictive-maintenance
title: Reference Architecture — Predictive Maintenance Copilot
type: reference-architecture
industry: manufacturing
ai_stage: 3
use_case_type: ["predictive-maintenance", "time-series", "copilot"]
tags: ["manufacturing", "iot", "time-series", "copilot", "rag"]
contributor: demo
updated_at: "2026-05-18"
---

# Predictive Maintenance Copilot

A reference architecture pairing a time-series anomaly model with a knowledge
copilot that helps technicians interpret alerts and find the right procedure.
Targets stage 3 manufacturers with sensor data and a maintenance backlog.

## Architecture

1. **Signals** — Equipment telemetry streams to a time-series store; an anomaly
   model flags drift and predicts remaining useful life.
2. **Knowledge base** — Maintenance manuals, past work orders, and failure
   write-ups are chunked and embedded with equipment metadata.
3. **Copilot** — When an alert fires, the copilot retrieves the relevant
   procedure and similar past failures, then drafts a triage plan with parts and
   steps.
4. **Feedback** — Technician outcomes feed back as new work-order records,
   improving retrieval over time.

## Controls

- The anomaly model owns the alert; the copilot is advisory.
- Procedures are cited verbatim from approved manuals — no paraphrased safety steps.
- Out-of-distribution alerts are escalated to a human, not auto-resolved.

## When to use

Plants with historized sensor data and a documented maintenance corpus. Not a
replacement for safety-critical control systems.

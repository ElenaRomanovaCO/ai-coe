---
id: reg-fda-ai-ml
name: FDA — AI/ML in Medical Devices
geo: us-federal
industry_scope: ["healthcare"]
status: in-effect
effective_date: null
risk_tier: "device class (I / II / III)"
tags: ["fda", "samd", "medical-devices", "healthcare", "pccp"]
---

# FDA Oversight of AI/ML Medical Devices

When AI software meets the definition of a medical device (Software as a Medical
Device, SaMD), the FDA regulates it. Risk-based device classification drives the
regulatory pathway.

## Key concepts

- **SaMD** — Software intended for a medical purpose may be a regulated device.
- **Risk classification** — Class I/II/III by intended use and risk; higher classes
  face more scrutiny (510(k), De Novo, or PMA pathways).
- **Predetermined Change Control Plan (PCCP)** — A mechanism to pre-authorize certain
  model updates so adaptive systems can be modified within agreed bounds.
- **Good Machine Learning Practice (GMLP)** — Principles for development and validation.

## What this means for engagements

Determine early whether a healthcare use case is SaMD — "decision support" vs.
"diagnosis" is a meaningful line. If it is a device, the regulatory pathway shapes the
whole program. Many CoE-built tools deliberately stay advisory (human-in-the-loop) to
remain outside device regulation; document that boundary.

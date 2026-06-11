---
id: qa-bedrock-provisioned-throughput
question: How do I size Bedrock provisioned throughput for a steady production workload?
tags: ["bedrock", "cost", "throughput", "production"]
posted_by: demo
posted_at: "2026-05-12T14:20:00Z"
answers:
  - id: ans-1
    text: "Start on on-demand and measure real tokens/sec at peak before committing. Provisioned throughput (model units) only pays off once sustained utilization is high; below roughly 40-50% utilization on-demand is usually cheaper. Size to the p95 of observed peak, not the absolute max."
    posted_by: demo
    posted_at: "2026-05-12T15:02:00Z"
  - id: ans-2
    text: "Watch the commitment term — model units bill whether you use them or not, so a 1-month commit on a bursty workload wastes money. For spiky traffic, keep on-demand and add a concurrency/latency budget instead."
    posted_by: demo
    posted_at: "2026-05-13T09:40:00Z"
---

# How do I size Bedrock provisioned throughput for a steady production workload?

A consultant asked how to decide between on-demand and provisioned throughput on Bedrock,
and how to size model units.

## Answers

**demo** — Start on on-demand and measure real tokens/sec at peak before committing.
Provisioned throughput (model units) only pays off once sustained utilization is high;
below roughly 40-50% utilization on-demand is usually cheaper. Size to the p95 of observed
peak, not the absolute max.

**demo** — Watch the commitment term — model units bill whether you use them or not, so a
1-month commit on a bursty workload wastes money. For spiky traffic, keep on-demand and add
a concurrency/latency budget instead.

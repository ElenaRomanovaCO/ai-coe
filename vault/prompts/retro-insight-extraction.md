---
id: prompt-retro-insight-extraction
title: Retrospective Insight Extraction
use_case: "Extract reusable insights and action items from engagement retro notes"
model_targets: ["sonnet-4-6", "haiku-4-5"]
variables: ["retro_notes", "engagement_type"]
version: 1
parent_id: null
---

# Retrospective Insight Extraction

## Prompt

From these engagement retrospective notes for a **{{engagement_type}}** engagement:
**{{retro_notes}}**, extract structured insights.

Produce:

1. **What worked** — patterns worth reusing, phrased as reusable guidance.
2. **What didn't** — root causes, not just symptoms.
3. **Reusable assets** — anything that should become a template, checklist, or pattern
   in the vault, with a suggested title and content type.
4. **Action items** — concrete, owned, and time-bound.

## Guidance

Generalize lessons so they apply beyond this one engagement. Do not include any client
names or identifying details — phrase everything generically. Flag candidate assets so
they can flow into the Knowledge Contribution module.

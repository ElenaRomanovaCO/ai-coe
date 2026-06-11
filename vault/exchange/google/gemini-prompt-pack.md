---
id: exch-google-gemini-prompt-pack
content_type: exchange
name: "Gemini Prompt Pack — Code & RAG"
tool: google
category: prompt-pack
summary: "Reusable Gemini prompts for code review, test generation, and grounded RAG answers over project docs."
tags: [gemini, prompts, rag, code-review, google]
install: |
  1. Copy the pack into `prompts/gemini/` in your repo (or a shared snippets store).
  2. Each prompt is parameterized (`{{language}}`, `{{context}}`, `{{question}}`) — fill and
     send via the Gemini CLI, Gemini Code Assist chat, or the Vertex/Gemini API.
  3. For RAG prompts, pass retrieved chunks in the `{{context}}` slot and instruct
     "answer only from context; cite sections."
source_url: "https://ai.google.dev/gemini-api/docs/prompting-strategies"
---

# Gemini Prompt Pack — Code & RAG

A small, opinionated set of Gemini prompts the team can reuse across the Gemini CLI, Gemini
Code Assist, and direct API calls — the Google-side counterpart to the cross-tool RAG pack.

## What it includes

- **Code review** — structured findings (severity, file/line, fix) for a supplied diff.
- **Test generation** — unit + edge-case tests for a given function/spec.
- **Grounded RAG** — answer strictly from supplied context with section citations and an
  explicit "not in the provided material" fallback.

## When to use

To get consistent, grounded Gemini output across tools instead of ad-hoc prompting — handy
when mixing the Gemini CLI for terminal work and Code Assist in the IDE.

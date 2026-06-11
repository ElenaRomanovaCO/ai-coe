---
id: exch-generic-rag-prompt-pack
content_type: exchange
name: "Cross-Tool RAG Prompt Pack"
tool: generic
category: prompt-pack
summary: "Tool-agnostic prompts for grounded retrieval Q&A: citation, refusal, and synthesis patterns."
tags: [rag, prompts, cross-tool, grounding]
install: |
  1. Copy the prompts into your tool of choice (Claude Code, Copilot, Cowork, Kiro).
  2. Wire the {context} and {question} placeholders to your retrieval step.
  3. Tune the citation and refusal wording to your domain.
source_url: ""
---

# Cross-Tool RAG Prompt Pack

A set of tool-agnostic prompts for retrieval-augmented Q&A that hold up across agents:
how to cite sources by id, when to refuse rather than guess, and how to synthesize an
answer from multiple chunks without inventing facts.

## What it does

- Provides a grounded-answer prompt with explicit citation rules.
- Includes a refusal pattern for out-of-context questions.
- Adds a multi-chunk synthesis prompt that avoids over-claiming.

## When to use

Any time you build a RAG flow and want consistent grounding behavior regardless of the
underlying tool. Adapt the citation format to your source ids.

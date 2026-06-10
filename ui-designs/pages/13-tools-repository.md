# Page Brief — Skills & Tools Repository

> Inherits `../design-system.md`. Route: `/modules/tools`. Module 7 (AGENT-08), Wave 4.
> Covers FR-032..033.

## Purpose

Browse and get recommendations for tools/frameworks fit to a context, stage, and
constraints. Like the Asset Library, but for tooling — plus a "recommend for my scenario"
mode.

## Content & data (real tool fields)

Tool entries: `name`, `category` (framework / vector-db / llm-provider / orchestration /
evals / guardrails / deployment), `stack[]`, `ai_stage_fit[]`, `cost_model` (open-source /
free-tier / usage-based / subscription / enterprise), `limitations[]`, `tags[]`. (Seed:
LangChain, LlamaIndex, Pinecone, S3 Vectors, Bedrock, Strands.)

## Primary actions

- **Recommend:** describe a scenario (stage, constraints) → ranked tool suggestions with
  rationale + caveats.
- **Browse/filter** by category, cost model, stage fit, stack.
- **Open** a tool → detail (best-fit scenarios, stage relevance, limitations).
- Compare a couple of tools side by side (light).

## States

Browse (cards) · filtered · recommend-results · detail · empty.

## Layout

Top: recommend bar + filters (category, cost, stage). Main: tool cards (name, category
badge, cost-model chip, stage-fit indicator, a key limitation). Detail = the tool brief.

## Design prompt seed

> Design a "Skills & Tools Repository" page for an enterprise AI-consulting platform. Top:
> a "recommend a tool for my scenario" input (AI stage + constraints) and filters for
> category, cost model, and stage fit. Main: a grid of tool cards — each shows the tool
> name (LangChain, Pinecone, AWS Bedrock, S3 Vectors, Strands Agents, …), a category badge
> (framework / vector-db / llm-provider / orchestration), a cost-model chip (open-source /
> usage-based), a compact 0–5 stage-fit indicator, and one key limitation. Also show a
> "recommended for your scenario" results state with ranked tools + a one-line rationale
> and caveat each. Clean, technical-but-approachable; indigo accent + muted category
> colors; Inter; rounded-lg; light + dark. No company names.

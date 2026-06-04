# Task: Wave 1 — Vault Seed Content

> **Phase:** 1
> **Feature group:** Wave 1 (Foundation)
> **Covers:** FR-005 (agents.md operational), enables FR-006 through FR-077 retrieval
> **Builds:** no agents (content only)
> **Depends on:** 00_foundation
> **Blocks:** 02 (Chat needs retrievable content), 03 (Asset Library renders it)
> **Estimated effort:** 1-2 days solo
> **Status:** ☐ Not started

---

## A. TL;DR Checklist

**Goal:** Populate the S3 vault bucket with ~30-40 curated demo markdown files across content types so Chat, Asset Library, and downstream modules have something real to read from day one.

**Build steps:**

1. **Author seed assets** (~10 reference architectures, solution patterns, kickoff templates across industries: healthcare, fintech, retail, manufacturing) → Verify: each has valid frontmatter per schema; re-embed pipeline indexes all.
2. **Author seed tools entries** (~6 tools: LangChain, LlamaIndex, Pinecone, S3 Vectors, Bedrock, Strands Agents) → Verify: filterable by category and stage.
3. **Author seed vendor evaluations** (~5: GPT-4o vs Claude Sonnet vs Gemini; pgvector vs Pinecone vs S3 Vectors) → Verify: structured comparison frontmatter validates.
4. **Author seed regulations** (~8: EU AI Act risk tiers, HIPAA AI guidance, NIST AI RMF, SEC AI guidance, GDPR AI implications, CA SB-1001, FDA AI/ML for medical devices, FFIEC AI for financial services) → Verify: searchable by geography + industry.
5. **Author seed feed items** (~10 with "what this means" commentary, mock dated) → Verify: feed renders with categories.
6. **Author seed prompts** (~5: client kickoff workshop facilitation, use case prioritization, executive briefing, risk assessment, retro extraction) → Verify: each loads in prompt studio.
7. **Author 1-2 sample assessments + 1 sample kit + 1 sample decision** for demo continuity → Verify: visible after login.
8. **Populate modules.json with all 27 module entries** (enabled=false initially) → Verify: schema validates; loader reads all 27.

**Files to create/edit:**

- `vault/assets/{industry}/{stage}/*.md` — reference architectures, patterns, templates
- `vault/tools/*.md` — tool entries
- `vault/vendors/*.md` — vendor/model evaluations
- `vault/regs/{geo}/{topic}/*.md` — regulation entries (focused on fintech, healthcare, PII)
- `vault/feed/{yyyy-mm}/*.md` — intelligence feed items
- `vault/prompts/*.md` — prompt templates
- `vault/assessments/demo-user/sample-{n}.md` — 1-2 sample completed assessments
- `vault/kits/demo-user/sample-kit/` — 1 sample kit folder
- `vault/decisions/sample-decision.md` — 1 sample decision entry
- `vault/modules.json` — populate all 27 entries
- `scripts/validate_vault.py` — pre-commit validator for frontmatter schemas

**Done when:**

- [ ] Vault contains 40+ markdown files across all content types
- [ ] All frontmatter validates against per-type Pydantic schemas
- [ ] modules.json contains all 27 entries (enabled=false for all)
- [ ] Re-embed Lambda has indexed every file (verify: `aws s3vectors query-vectors` returns at least 1 result per content type with a relevant query)
- [ ] Validator script blocks commits with malformed frontmatter
- [ ] No company names, no real PII, no real client data anywhere

---

## B. Standalone Prompt

### START STANDALONE PROMPT

You are populating the **seed content vault** for the AI CoE Platform. Task 00 (Foundation) is complete: S3 vault bucket, S3 Vectors index, ReEmbed Lambda, modules.json schema, agents.md all exist. Now you are adding the actual content.

#### Project context

- Platform: internal multi-agent platform for consultants at AI-focused IT consulting firms. 27 modules, generic naming, no company references.
- Stack: Python + AWS Strands + Bedrock + Next.js 16 + S3 + S3 Vectors. CDK Python infra. Single AWS account, us-east-1.
- This task adds no code. It adds curated demo content to the vault bucket.

#### What you are building

**Goal:** A working knowledge base with realistic but generic content covering the demo industries (fintech, healthcare, retail, manufacturing) and the demo themes (PII handling, governance, AI maturity stages 0-5).

**Functional requirements supported:**

- FR-005: agents.md controls Chat behavior (already in place from task 00; this task verifies it loads cleanly with surrounding content)
- All retrieval-dependent FRs: FR-003, FR-006-008, FR-010-015, FR-018, FR-023-024, FR-029-031, FR-041, FR-045-050, FR-058, FR-073, plus implicit support for every module

#### Frontmatter schemas (per content type)

Define one Pydantic schema per content type in `agents/lib/schemas/`:

```python
class AssetFrontmatter(BaseModel):
    id: str                                       # slug
    title: str
    type: Literal["reference-architecture", "solution-pattern", "kickoff-template", "discovery-questionnaire", "workshop-agenda", "roi-template", "risk-checklist"]
    industry: Literal["financial-services", "healthcare", "retail", "manufacturing", "energy", "public-sector", "technology", "professional-services", "cross-industry"]
    ai_stage: int                                 # 0-5
    use_case_type: list[str]                      # tags
    tags: list[str]
    contributor: str = "demo"
    updated_at: str                               # ISO date

class ToolFrontmatter(BaseModel):
    id: str
    name: str
    category: Literal["framework", "vector-db", "llm-provider", "orchestration", "evals", "guardrails", "deployment"]
    stack: list[str]                              # languages, runtimes
    ai_stage_fit: list[int]                       # which stages it serves
    cost_model: Literal["open-source", "free-tier", "usage-based", "subscription", "enterprise"]
    limitations: list[str]
    tags: list[str]

class VendorEvalFrontmatter(BaseModel):
    id: str
    category: Literal["llm-provider", "vector-db", "cloud-ai-platform", "orchestration-framework"]
    vendors_compared: list[str]
    criteria: list[str]
    last_verified: str

class RegulationFrontmatter(BaseModel):
    id: str
    name: str
    geo: Literal["eu", "us-federal", "us-state-ca", "us-state-ny", "uk", "canada", "global"]
    industry_scope: list[str]
    status: Literal["proposed", "enacted", "in-effect", "superseded"]
    effective_date: str | None
    risk_tier: str | None
    tags: list[str]

class FeedItemFrontmatter(BaseModel):
    id: str
    title: str
    category: Literal["model-release", "tool-launch", "research", "vendor-update", "industry-news"]
    source_url: str
    published_at: str
    industries: list[str]
    tags: list[str]
    radar_status: Literal["adopt", "trial", "assess", "hold"] | None

class PromptFrontmatter(BaseModel):
    id: str
    title: str
    use_case: str
    model_targets: list[str]
    variables: list[str]
    version: int = 1
    parent_id: str | None = None                  # for forks
```

#### Implementation steps

1. **Write the validator script** (`scripts/validate_vault.py`): walks `vault/`, parses each .md file's frontmatter, validates against the matching schema by folder, exits non-zero on any failure. Wire as pre-commit hook.

2. **Author 10 seed assets** across industries and stages. Examples:
   - `vault/assets/healthcare/2/reference-arch-clinical-notes-rag.md` — RAG pattern for clinical notes
   - `vault/assets/financial-services/3/solution-pattern-fraud-scoring-agent.md`
   - `vault/assets/cross-industry/1/kickoff-template-discovery-workshop.md`
   - `vault/assets/retail/2/use-case-product-recommendations.md`
   - etc.
   Each file: 200-500 words, real-feeling content, no firm names, generic personas.

3. **Author 6 seed tools** under `vault/tools/`. Cover: LangChain, LlamaIndex, Pinecone, S3 Vectors, AWS Bedrock, Strands Agents. Each with description, best-fit scenarios, stage relevance, limitations.

4. **Author 5 seed vendor evals** under `vault/vendors/`. Examples: LLM provider comparison (Claude vs GPT vs Gemini for document analysis), vector DB comparison (Pinecone vs pgvector vs S3 Vectors), orchestration framework comparison.

5. **Author 8 seed regulations** under `vault/regs/{geo}/{topic}/`. Coverage: EU AI Act (risk tiers), HIPAA + AI for medical devices, NIST AI RMF, SEC AI guidance, GDPR + AI, California SB-1001, FDA AI/ML, FFIEC AI for financial services. Focus on the fintech / healthcare / PII themes per the brief Q3 decision.

6. **Author 10 seed feed items** under `vault/feed/{yyyy-mm}/`. Mix of model releases, tool launches, research, vendor updates. Include a CoE-style "what this means" section in each. Dated within the past quarter.

7. **Author 5 seed prompts** under `vault/prompts/`. Real-feeling consulting prompts: client kickoff workshop facilitation, use case prioritization workshop, executive briefing draft, AI risk assessment scaffolding, retro insight extraction.

8. **Author 1-2 sample completed assessments** under `vault/assessments/demo-user/` so Chat has something to demonstrate.

9. **Author 1 sample kit** under `vault/kits/demo-user/sample-kit/` with a README and 3-5 linked assets.

10. **Author 1 sample decision** under `vault/decisions/`.

11. **Populate modules.json** with all 27 module entries. For each: id, name, wave, purpose, when_to_use (3 examples each), example_queries (3-5 per module), agent_id, model_tier, worker_ids, enabled=false.

12. **Validate everything**:
    - `python scripts/validate_vault.py` exits 0
    - Sync vault folder to S3 with `aws s3 sync vault/ s3://{vault_bucket}/`
    - Wait 90s for re-embed to finish
    - For each content type, run a representative S3 Vectors query and confirm at least one hit per type

#### Definition of done

- [ ] 40+ markdown files in vault with valid frontmatter
- [ ] modules.json has all 27 entries, validated
- [ ] Every content type returns hits in S3 Vectors
- [ ] validate_vault.py exits 0
- [ ] All content uses generic names, no PII, no real client references
- [ ] DoD checklist from `00_foundation.md` Behavioral guardrails passed

#### Behavioral guardrails

Same as task 00 Section "Behavioral guardrails for this task" (carry forward).

#### Out of scope

- Module agent code (later wave tasks)
- UI rendering of any content (later wave tasks)
- Real ingestion from RSS / arXiv / regulatory APIs (post-demo-plan.md Section 3)

### END STANDALONE PROMPT

---

## C. Notes & Decisions Log
- 2026-06-03: created. Seed scope per brief Q3 and Wave 1 plan.

## D. References
- Brief: `ai_docs/brief.md` Sections 4.2 (downscoped to seeded data), 5 (FRs), 15 (Wave 1)
- Design: `ai_docs/design.md` Sections 4 (S3 Vault Bucket), 6 (Flow 2 ingestion)
- Foundation: `ai_docs/tasks/00_foundation.md`

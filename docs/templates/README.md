# Templates — Project Ideation → Plan → Tasks

A three-stage workflow for taking an AI/agentic project from raw idea to executable task prompts, using Claude Code.

---

## The workflow

```
┌─────────────────────────────────────────────────────────────────┐
│  Stage 1: Brainstorm                                            │
│  Paste: Templates/01_brainstorm_brief.md                        │
│  Claude asks: identity, goal, users, FRs, NFRs, agents, infra,  │
│               security, observability, integrations, phasing... │
│  Saves to:    ai_docs/brief.md                                  │
└─────────────────────────────────────────────────────────────────┘
                            ↓
                  (you review the brief)
                            ↓
┌─────────────────────────────────────────────────────────────────┐
│  Stage 1.5a: System Design  (OPTIONAL)                          │
│  Paste: Templates/02a_generate_system_design.md                 │
│  Claude surfaces 2-4 architectural decisions for sign-off,      │
│  drafts a layered Mermaid diagram, runs risk assessment,        │
│  self-critiques. Use for agent-heavy / multi-service projects.  │
│  Saves to: ai_docs/design.md                                    │
└─────────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────────┐
│  Stage 1.5b: UI Requirements  (OPTIONAL)                        │
│  Paste: Templates/02b_generate_ui_requirements.md               │
│  Claude elicits workflows, UI architecture, visual basics, and  │
│  (key for agentic products) decisions on where agents appear,   │
│  what users see, control, and approval flows. Self-critiques.   │
│  Saves to: ai_docs/ui_requirements.md                           │
└─────────────────────────────────────────────────────────────────┘
                            ↓
            (you review design + UI requirements)
                            ↓
┌─────────────────────────────────────────────────────────────────┐
│  Stage 2: Implementation Plan                                   │
│  Paste: Templates/02_generate_implementation_plan.md            │
│  Claude reads brief (plus design.md and ui_requirements.md if   │
│  present), surfaces architectural decisions for sign-off,       │
│  drafts a feature-grouped plan, self-critiques it.              │
│  Saves to: ai_docs/plan.md                                      │
└─────────────────────────────────────────────────────────────────┘
                            ↓
                   (you review the plan)
                            ↓
┌─────────────────────────────────────────────────────────────────┐
│  Stage 3: Task Files                                            │
│  Paste: Templates/03_generate_tasks.md                          │
│  Claude generates one task file per feature group, each with    │
│  both a TL;DR checklist AND a fully standalone paste-and-go     │
│  prompt for fresh sessions.                                     │
│  Saves to: ai_docs/tasks/INDEX.md + ai_docs/tasks/NN_*.md       │
└─────────────────────────────────────────────────────────────────┘
                            ↓
        (execute tasks in fresh sessions or running session)
```

---

## Files in this folder

| File | When to use it |
|---|---|
| `01_brainstorm_brief.md` | Starting a new project from scratch. Captures everything. |
| `02a_generate_system_design.md` | (Optional) After brief is locked, for agent-heavy or multi-service projects that deserve a dedicated architecture session before the full plan. |
| `02b_generate_ui_requirements.md` | (Optional) After brief (and design, if running 02a). Elicits workflows, UI architecture, and agent-UX decisions before wireframing. Especially useful for agentic products. |
| `02_generate_implementation_plan.md` | After brief is reviewed and locked (plus design and UI requirements, if you ran 02a / 02b). |
| `03_generate_tasks.md` | After plan is reviewed and approved. |
| `karpathy-guidelines.md` | Shared behavioral rulebook referenced by all stages. Don't edit unless intentional. |
| `CLAUDE.md.template` | Generic project-level context file. Copy to `<project-root>/CLAUDE.md`, replace `{PLACEHOLDERS}` in the project overview and stack sections, leave methodology sections as-is. |

---

## Output structure in your project

After running all three stages, your project will have:

```
ai_docs/
  ├── brief.md                         # filled by Stage 1
  ├── design.md                        # filled by Stage 1.5a (optional)
  ├── ui_requirements.md               # filled by Stage 1.5b (optional)
  ├── plan.md                          # filled by Stage 2
  └── tasks/
      ├── INDEX.md                     # filled by Stage 3
      ├── 01_{feature_slug}.md
      ├── 02_{feature_slug}.md
      └── ...
```

You can override these paths if you say so during a session.

---

## Conventions used across all three templates

- **Stable IDs:** `FR-001`, `NFR-001`, `AGENT-01`, `INT-01`, `RISK-01`, `Q-01`. Tasks trace back to these.
- **Default stack bias:** AWS-native + Strands Agents + Bedrock + Python/FastAPI + Next.js. Always confirmable/overridable.
- **MCP-aware blocks:** Each template has an optional block that activates if MCP servers like Context7, AWS Docs, Strands docs, AWS CDK, Fetch are connected. Templates also work without any MCP.
- **Feature-grouped phases, not layer-grouped.** Phase 1 ships a working slice (DB + API + UI + agent), not "the whole backend."
- **Karpathy guardrails enforced at every stage.** Surface assumptions, simplicity first, surgical changes, verifiable acceptance criteria.

---

## Customizing for a specific project

For one-off project tweaks, edit the filled brief/plan/tasks in `ai_docs/`. Leave templates in this folder generic.

If you find yourself making the same edit to a template across many projects (e.g., you always want a specific section added), edit the template here so it propagates to future projects.

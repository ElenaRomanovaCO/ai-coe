# Design System — AI CoE Platform

The shared visual language for every page. Paste this as context whenever you
generate a page design so the look and feel stays cohesive.

## Product & audience

An internal platform for **consultants at an AI-focused IT consulting firm**. Think of
it as a *senior consultant's cockpit*: a single place to assess clients, pull reusable
assets, check governance/compliance, and chat with a knowledgeable copilot over a
markdown knowledge base.

Users are **busy experts** who skim, compare, and act. They value speed, trust, and
clarity over decoration. Desktop-first, fully responsive.

## Personality

Professional · trustworthy · calm · modern. Enterprise SaaS, not a consumer app.
Confident and quiet — information-dense but breathable. The product should feel like a
tool a senior advisor would happily demo to a client.

Avoid: playful gradients everywhere, neon, heavy skeuomorphism, clutter, marketing
fluff.

## Visual direction

- **Palette (starting point — adjustable):**
  - Neutral base: slate / cool gray (`slate-50` surfaces → `slate-900` text).
  - Primary accent: **deep indigo** (trust + intelligence) — used for primary actions,
    active nav, links, focus rings.
  - Semantic: success = green, warning = amber, danger = red, info = blue.
  - Light mode is primary; support dark mode.
- **Content-type accents** (recurring motif — each KB content type gets a consistent
  color + lucide icon): asset, tool, vendor, reg, feed, prompt, decision, assessment,
  kit. Keep them distinct but muted (used in badges/icons, not big fills).
- **AI maturity stage scale (0–5)** is a recurring element — design a compact,
  reusable **stage indicator** (e.g. a 6-segment bar or pill) used across assessment,
  dashboard, and asset cards.
- **Wave numbers (1–7)** tag modules; show as small neutral chips.
- **Wordmark:** the product is branded **"Praxis"** in the UI (established by the
  generated designs in `designs/`). Use it as the app's name/logo.
- **Typography:** **Hanken Grotesk** (the generated designs use it; load via Google
  Fonts). Inter/system UI is an acceptable fallback. Strong hierarchy: large semibold
  headings, comfortable body, smaller muted metadata. **Monospace** for IDs, file
  paths, and code.
- **Source of truth for exact tokens:** the self-contained `designs/*(offline).html`
  renders contain the real CSS (colors, radii, spacing). When in doubt about an exact
  value, read those over this summary.
- **Shape & depth:** rounded corners (`rounded-lg`, ~8–12px), hairline borders
  (`border-slate-200`), soft shadows on raised surfaces. 8px spacing grid.
- **Icons:** lucide-react, consistent stroke weight.
- **Motion:** subtle and purposeful — streaming text, hover lifts, 150–200ms
  transitions, skeleton loaders. Never gratuitous.

## Layout

- **App shell:** top header (product mark + current user + logout) · left sidebar nav
  (modules) · main content area.
- **Chat Copilot dock:** ALWAYS present, fixed bottom-right, collapsible. It is the
  product's signature element and front door — design every page assuming the dock can
  overlay the bottom-right corner.
- Max content width ~1200–1400px, centered, generous gutters.

## Components (shadcn/ui)

Button, Card, Input, Badge, Table, Tabs, Sheet/Dialog, Tooltip, DropdownMenu, Skeleton,
Avatar, Separator, ScrollArea. Prefer composing these over bespoke widgets.

## Standard states (design every page for all four)

- **Empty** — friendly, with a clear next action.
- **Loading** — skeletons that match the final layout (no spinners-only).
- **Error** — calm, plain-English, with a retry path; never a raw stack trace.
- **Populated** — the real, data-rich view.

## Accessibility

WCAG 2.1 AA. Full keyboard navigation, visible focus rings (indigo), sufficient
contrast, semantic landmarks, labelled controls, respects reduced-motion.

## Tech constraints (so designs are implementable)

Next.js 16 (App Router, RSC) · React 19 · Tailwind CSS v4 · shadcn/ui · lucide-react.
Password-gated (single shared password). Server-rendered on AWS Amplify. Designs should
map to Tailwind utilities and shadcn components.

## Data motifs to reflect (use real shapes)

- **Asset** frontmatter: `title`, `type` (reference-architecture / solution-pattern /
  kickoff-template / …), `industry`, `ai_stage` (0–5), `use_case_type[]`, `tags[]`,
  `updated_at`.
- **Module** registry: `id` (module-N), `name`, `wave` (1–7), `purpose`, `agent_id`,
  `enabled` (true/false — disabled modules render as "coming soon").
- **Citation** (from chat): `file_path`, `content_type`, `score`, optional
  `asset_library_url`.

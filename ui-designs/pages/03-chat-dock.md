# Page Brief — Chat Copilot Dock

> Inherits `../design-system.md`. Global component, present on every authenticated page.
> Module 9 / AGENT-01. The product's signature surface. (Already live — this brief is to
> elevate its design.)

## Purpose

The always-available conversational front door. Routes intent across modules, answers
knowledge questions with **streamed, cited** responses, and surfaces module actions. It
must feel fast, trustworthy, and effortless.

## Who & when

Any user, anywhere in the app, who wants to ask, find, or do something without
navigating. Often used side-by-side with a page (e.g. reading an asset).

## Content & data

- **Collapsed:** a floating action button (FAB) bottom-right — sparkles/chat icon,
  subtle label or pulse, unread/active hint if streaming.
- **Expanded panel:** header (title "Copilot", new-chat, minimize), a scrollable
  **transcript**, and a composer (text input + send/stop).
- **Message types:**
  - User bubble.
  - Assistant message — **streams token-by-token**; supports markdown (lists, tables,
    bold, code).
  - **Tool indicator** — a slim "🔎 searching the knowledge base…" / "describing
    module…" line while a tool runs.
  - **Citation badges** — under an assistant message, chips showing `file_path`'s
    basename + a content-type icon + relevance hint; click → opens the asset
    (`asset_library_url` / file path). This is a key trust signal — make citations feel
    first-class.
  - **Module cards / UI actions** — when the agent suggests a module (e.g. "start a
    maturity assessment"), render a small actionable card.
- **Composer:** multiline input, send button, **Stop** button while streaming.

## Primary actions

Send a message · Stop a stream · click a citation → open asset · click a module card →
navigate/act · new chat · minimize. Session + transcript persist per browser tab
(survive refresh); a new tab = a new session.

## States

- Collapsed FAB · expanding/expanded.
- **Streaming** (tokens flowing, Stop available, tool indicator) — the hero interaction;
  make incremental streaming visibly delightful.
- Idle with history.
- **Empty** — a friendly first-run with 3–4 example prompts ("What does Module 4 do?",
  "Find a healthcare reference architecture", "List the wave 3 modules").
- **Error** — calm inline message (e.g. transient backend issue) with retry; never a
  raw error.
- Guardrail refusal — render the refusal plainly, not as an error.

## Layout

Fixed bottom-right. Collapsed: ~56px FAB. Expanded: a panel ~380–440px wide ×
~560–640px tall (responsive; on mobile it can go near-fullscreen as a sheet). Transcript
scrolls; composer pinned to the bottom; header pinned to the top.

## Components

FAB (Button), Card/Sheet (panel), message bubbles, streaming text, Badge (citations),
small action Card (module suggestions), Textarea, Button (send/stop), Tooltip,
ScrollArea, Skeleton/typing indicator.

## Visual direction

Light, fast, and trustworthy. The streaming answer + citation chips are the stars — give
them polish (smooth token reveal, citations that look authoritative). Quiet chrome so the
conversation leads. A touch of the indigo accent (send button, links, active states).

## Design prompt seed

> Design a floating "Copilot" chat dock for an enterprise AI-consulting platform,
> pinned to the bottom-right and present on every page. Show: (1) the collapsed state —
> a circular indigo FAB with a sparkles icon; (2) the expanded panel (~400×620px) with a
> slim header ("Copilot" + new-chat + minimize), a scrollable transcript, and a composer
> (multiline input + send button). In the transcript, show a realistic conversation: a
> user message; an assistant answer rendered in markdown that is mid-stream (a few words
> still appearing) with a subtle "🔎 Searching the knowledge base…" tool indicator above
> it; and beneath the answer, a row of clickable **citation chips** (file-path basename +
> content-type icon + relevance), plus one small actionable "Start a maturity assessment"
> module card. Include a Stop button shown during streaming. Also show the empty
> first-run state with 3–4 example-prompt chips, and a calm inline error state. Fast,
> trustworthy, quiet chrome, indigo accent, Inter, rounded-lg, soft shadow, light + dark.
> Generic demo content, no company names.

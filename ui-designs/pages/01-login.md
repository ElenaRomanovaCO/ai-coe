# Page Brief — Login

> Inherits `../design-system.md`. Route: `/login`. Covers FR-001.

## Purpose

The single shared password gate. First impression of the product — must feel
trustworthy and premium in five seconds. The user enters a shared password and a
display name (no real accounts; demo gate).

## Who & when

A consultant opening the platform (often to demo it). They want in fast. Likely on a
laptop, sometimes shared-screen.

## Content & data

- Product mark + name ("AI CoE Platform" or a generic wordmark) and a one-line tagline
  (e.g. "Your center of excellence, on tap").
- **Password** field (single shared password).
- **Display name** field (stored in browser localStorage; shown later in the header).
- Primary "Enter" button.
- Subtle note that this is an internal/demo environment.

## Primary actions

- Submit password + name → on success, redirect to `/dashboard`.
- Show inline error on wrong password (stay on page).

## States

- **Default** — clean, inviting.
- **Error** — wrong password: a calm inline message under the field, field highlighted,
  no layout jump.
- **Loading** — button shows a spinner / disabled while validating.

## Layout

A centered card (max ~420px) on a branded full-bleed background — a restrained
indigo/slate gradient or a subtle abstract "knowledge graph / nodes" motif (very
muted). Card: logo, tagline, two fields, button. Everything vertically centered.

## Components

Card, Input (x2), Button, a small inline Alert for errors, lucide lock/sparkles icon.

## Visual direction

Minimal and confident — lots of whitespace, one focal card, a hint of the brand accent.
"A members' entrance," not a marketing splash. Dark-mode variant welcome.

## Design prompt seed

> Design a login screen for an internal enterprise "AI Center of Excellence" platform
> used by consultants. Centered card (~420px) on a restrained indigo-to-slate
> background with a very subtle abstract node/graph motif. Card contains: a small
> generic wordmark + sparkles/lock icon, a one-line tagline, a password field, a
> display-name field, and a full-width indigo "Enter" button. Calm, premium, trustworthy
> enterprise SaaS aesthetic; Inter font; rounded-lg corners; soft shadow. Show the
> default state and the wrong-password error state (inline, no layout shift). Light mode
> primary, also provide a dark variant. No company names.

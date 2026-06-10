# Page Brief — AI Project Health Monitor

> Inherits `../design-system.md`. Route: `/modules/project-health`. Module 18 (AGENT-17),
> Wave 5. Covers FR-051..053.

## Purpose

Assess the health of an in-flight AI delivery project and flag risks early — a RAG-status
dashboard for an engagement.

## Content & data

- **Projects:** a list with overall health (red/amber/green), name, stage, last updated.
- **Health signals:** dimensions (scope, data, timeline, adoption, governance) each with
  a status + note.
- **Risks:** emerging risks with severity + recommended action.
- **Trend:** health over time (sparkline/line).

## Primary actions

Pick a project · view health summary · drill into a signal/risk · acknowledge/assign a
risk · export a status.

## States

Project list · project detail (health) · empty · loading.

## Layout

Top: project picker + overall RAG status hero. Below: a grid of signal cards (each with
status), a risks list (severity-sorted), and a small trend chart.

## Design prompt seed

> Design an "AI Project Health Monitor" dashboard for an enterprise AI-consulting platform.
> Top: a project selector and a large overall RAG (red/amber/green) health status with a
> short summary. Below: a grid of health-signal cards (Scope, Data Readiness, Timeline,
> Adoption, Governance) each showing a green/amber/red status and a one-line note; a
> "risks" list sorted by severity with recommended actions and assign/acknowledge
> controls; and a small health-over-time trend line. Calm operational dashboard; clear
> status colors; indigo accent; Inter; rounded-lg; light + dark. Use a generic "retail
> recommendation project" example — no company names.

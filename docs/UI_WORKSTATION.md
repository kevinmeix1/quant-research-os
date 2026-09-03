# Quant Research OS — Workstation UI

Production-oriented research workstation (Next.js App Router) living in `web/`.

## Stages delivered

| Stage | Surface |
|------|---------|
| 1 | Application shell (collapsible nav, top bar, command bar) |
| 2 | Overview dashboard |
| 3 | Research workspace (question, workflow graph, agent inspector) |
| 4 | Experiment explorer + detail |
| 5–6 | Alpha Library + detail / lineage |
| 7–8 | Portfolio what-if + Risk center |
| 9–12 | Agent Activity, Reports, Research Memory, Paper Trading |
| 13–14 | ⌘K search, SSE `/events/stream`, design system, tests, build |

## Design

- Dark research-terminal aesthetic (IBM Plex Sans / Mono)
- Dense panels, semantic status badges, no decorative KPI chrome
- Explicit `BACKTEST` / `PAPER TRADING` / `LIVE` provenance banners
- Traceability: conclusion → experiment → agent payload

## Run

See `web/README.md`.

API CORS defaults include `http://127.0.0.1:3012`.

## Honesty notes

- Charts fall back to metric-conditioned series when equity curves are not yet attached to `/backtests/{id}`.
- Agents are currently deterministic (no live LLM); System page and agent inspector label this clearly.
- Paper trading remains simulation-labeled.

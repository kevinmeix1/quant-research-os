# Quant Research OS — Workstation UI

Institutional quantitative research workstation (Next.js).

## Run

```bash
# Terminal 1 — API
cd "/Users/kaiwenmei/Desktop/x11/trading operating system"
source .venv/bin/activate
quant serve --host 127.0.0.1 --port 8002

# Terminal 2 — UI
cd web
npm install
npm run dev
```

Open http://127.0.0.1:3012

Optional:

```bash
export NEXT_PUBLIC_QROS_API_URL=http://127.0.0.1:8002
export NEXT_PUBLIC_QROS_API_KEY=...   # if QROS_API_KEY set on API
```

## Architecture

```
web/src/
  app/           # pages (Overview, Research, Experiments, Alphas, …)
  components/    # shell, charts, research graph, UI primitives
  domain/        # typed models
  lib/           # API client, status, realtime SSE
  styles/        # design tokens + shell + components
```

## Shortcuts

- `⌘/Ctrl + K` — global command palette
- Bottom command bar — start research from a natural-language question

## Tests

```bash
npm test
npm run build
```

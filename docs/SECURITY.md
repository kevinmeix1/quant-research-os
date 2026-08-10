# Security

## Current posture (honest)

- Research-only; **no live trading tools**
- Optional `QROS_API_KEY` (enforced when set)
- CORS defaults to localhost origins
- SQL table/column allowlists in `ResearchDB`
- Dashboard HTML escaping for dynamic fields
- Agents cannot execute shell / arbitrary code

## Not yet production

- No JWT/RBAC
- Sync research can still DoS a process
- Paper path is IID noise (labeled), not broker-connected
- Secrets must never be placed in prompts (no LLM wired today)

## Recommended before internet exposure

1. Require API keys in all environments
2. Move research to a worker queue
3. Network policies: API private, UI public via gateway
4. Sandbox any future generated strategy code

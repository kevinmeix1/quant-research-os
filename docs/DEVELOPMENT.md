# Development

```bash
cd "/Users/kaiwenmei/Desktop/x11/trading operating system"
python3.11 -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
pytest
```

## Useful commands

```bash
quant research run "Find a robust cross-sectional FX strategy..."
quant serve --host 127.0.0.1 --port 8002
```

Optional API auth:

```bash
export QROS_API_KEY=dev-secret
# clients must send header: X-API-Key: dev-secret
```

## Data root

```bash
export QROS_DATA_ROOT=/tmp/qros_data
```

## Tests

- Unit: domain, costs, metrics, engines
- Invariants: `tests/test_quant_invariants.py`
- E2E: `tests/test_e2e_research.py`
- API: `tests/test_api.py`

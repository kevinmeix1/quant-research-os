# Deployment

## Status

No production containers yet. Local process deployment only.

## Local

```bash
quant serve --host 127.0.0.1 --port 8002
```

## Target topology (not implemented)

```
frontend (static) → API → worker(s) → SQLite/Postgres
                              ↓
                         object storage (parquet)
```

## Health

`GET /health` checks DB connectivity.

## Known gaps

- No Dockerfile / compose
- No migrations framework (schema via `CREATE IF NOT EXISTS`)
- No backup automation
- Full research resume-from-checkpoint not implemented (checkpoints saved; restart still re-runs)

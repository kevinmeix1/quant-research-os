"""SQLite metadata store — authoritative for research facts."""

from __future__ import annotations

import json
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterator

from quant_research_os.storage.paths import db_path

SCHEMA = """
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS research_requests (
  research_id TEXT PRIMARY KEY,
  payload TEXT NOT NULL,
  status TEXT NOT NULL,
  created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS research_plans (
  research_id TEXT PRIMARY KEY,
  payload TEXT NOT NULL,
  created_at TEXT NOT NULL,
  FOREIGN KEY (research_id) REFERENCES research_requests(research_id)
);

CREATE TABLE IF NOT EXISTS hypotheses (
  hypothesis_id TEXT PRIMARY KEY,
  research_id TEXT NOT NULL,
  payload TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS experiments (
  experiment_id TEXT PRIMARY KEY,
  research_id TEXT NOT NULL,
  payload TEXT NOT NULL,
  status TEXT NOT NULL,
  configuration_hash TEXT,
  created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS strategies (
  strategy_id TEXT PRIMARY KEY,
  payload TEXT NOT NULL,
  version TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS alphas (
  alpha_id TEXT PRIMARY KEY,
  strategy_id TEXT NOT NULL,
  payload TEXT NOT NULL,
  status TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS backtest_results (
  backtest_id TEXT PRIMARY KEY,
  experiment_id TEXT,
  payload TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS validation_results (
  validation_id TEXT PRIMARY KEY,
  experiment_id TEXT NOT NULL,
  payload TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS reviews (
  review_id TEXT PRIMARY KEY,
  payload TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS reports (
  research_id TEXT PRIMARY KEY,
  payload TEXT NOT NULL,
  decision TEXT NOT NULL,
  created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS agent_traces (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  research_id TEXT NOT NULL,
  agent TEXT NOT NULL,
  event_type TEXT NOT NULL,
  payload TEXT NOT NULL,
  created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS lineage_edges (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  src_type TEXT NOT NULL,
  src_id TEXT NOT NULL,
  rel TEXT NOT NULL,
  dst_type TEXT NOT NULL,
  dst_id TEXT NOT NULL,
  meta TEXT
);

CREATE TABLE IF NOT EXISTS paper_strategies (
  alpha_id TEXT PRIMARY KEY,
  payload TEXT NOT NULL,
  status TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS documents (
  document_id TEXT PRIMARY KEY,
  payload TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS events (
  event_id TEXT PRIMARY KEY,
  payload TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS research_memory (
  key TEXT PRIMARY KEY,
  kind TEXT NOT NULL,
  payload TEXT NOT NULL,
  updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS research_checkpoints (
  research_id TEXT PRIMARY KEY,
  node TEXT NOT NULL,
  payload TEXT NOT NULL,
  updated_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_experiments_research ON experiments(research_id);
CREATE INDEX IF NOT EXISTS idx_experiments_status ON experiments(status);
CREATE INDEX IF NOT EXISTS idx_alphas_status ON alphas(status);
CREATE INDEX IF NOT EXISTS idx_traces_research ON agent_traces(research_id);
CREATE INDEX IF NOT EXISTS idx_lineage_src ON lineage_edges(src_id);
CREATE INDEX IF NOT EXISTS idx_lineage_dst ON lineage_edges(dst_id);
CREATE INDEX IF NOT EXISTS idx_hypotheses_research ON hypotheses(research_id);
"""

_ALLOWED_TABLES = frozenset(
    {
        "research_requests",
        "research_plans",
        "hypotheses",
        "experiments",
        "strategies",
        "alphas",
        "backtest_results",
        "validation_results",
        "reviews",
        "reports",
        "agent_traces",
        "lineage_edges",
        "paper_strategies",
        "documents",
        "events",
        "research_memory",
        "research_checkpoints",
    }
)
_ALLOWED_KEYS = frozenset(
    {
        "research_id",
        "hypothesis_id",
        "experiment_id",
        "strategy_id",
        "alpha_id",
        "backtest_id",
        "validation_id",
        "review_id",
        "document_id",
        "event_id",
        "key",
    }
)


def _utcnow() -> str:
    return datetime.now(timezone.utc).isoformat()


class ResearchDB:
    def __init__(self, path: Path | None = None) -> None:
        self.path = Path(path) if path else db_path()
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._init()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(str(self.path), timeout=30.0)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        conn.execute("PRAGMA journal_mode = WAL")
        conn.execute("PRAGMA busy_timeout = 5000")
        return conn

    def _init(self) -> None:
        with self._connect() as conn:
            conn.executescript(SCHEMA)

    @contextmanager
    def conn(self) -> Iterator[sqlite3.Connection]:
        c = self._connect()
        try:
            yield c
            c.commit()
        finally:
            c.close()

    def _validate_table(self, table: str) -> None:
        if table not in _ALLOWED_TABLES:
            raise ValueError(f"table not allowlisted: {table}")

    def _validate_key(self, key_col: str) -> None:
        if key_col not in _ALLOWED_KEYS:
            raise ValueError(f"key column not allowlisted: {key_col}")

    def upsert_json(self, table: str, key_col: str, key: str, payload: dict[str, Any], **extra: Any) -> None:
        self._validate_table(table)
        self._validate_key(key_col)
        for k in extra:
            if not k.replace("_", "").isalnum():
                raise ValueError(f"invalid extra column: {k}")
        cols = [key_col, "payload", *extra.keys()]
        placeholders = ", ".join("?" for _ in cols)
        updates = ", ".join(f"{c}=excluded.{c}" for c in cols if c != key_col)
        values = [key, json.dumps(payload), *extra.values()]
        sql = (
            f"INSERT INTO {table} ({', '.join(cols)}) VALUES ({placeholders}) "
            f"ON CONFLICT({key_col}) DO UPDATE SET {updates}"
        )
        with self.conn() as c:
            c.execute(sql, values)

    def get_json(self, table: str, key_col: str, key: str) -> dict[str, Any] | None:
        self._validate_table(table)
        self._validate_key(key_col)
        with self.conn() as c:
            row = c.execute(f"SELECT payload FROM {table} WHERE {key_col}=?", (key,)).fetchone()
        return json.loads(row["payload"]) if row else None

    def list_json(self, table: str, where: str | None = None, params: tuple = ()) -> list[dict[str, Any]]:
        self._validate_table(table)
        sql = f"SELECT payload FROM {table}"
        if where:
            # Only allow simple equality filters on known columns
            allowed_where = {
                "research_id=?",
                "status=?",
                "strategy_id=?",
                "experiment_id=?",
            }
            if where not in allowed_where:
                raise ValueError(f"where clause not allowlisted: {where}")
            sql += f" WHERE {where}"
        with self.conn() as c:
            rows = c.execute(sql, params).fetchall()
        return [json.loads(r["payload"]) for r in rows]

    def add_trace(self, research_id: str, agent: str, event_type: str, payload: dict[str, Any]) -> None:
        with self.conn() as c:
            c.execute(
                "INSERT INTO agent_traces (research_id, agent, event_type, payload, created_at) VALUES (?,?,?,?,?)",
                (research_id, agent, event_type, json.dumps(payload), _utcnow()),
            )

    def list_traces(self, research_id: str) -> list[dict[str, Any]]:
        with self.conn() as c:
            rows = c.execute(
                "SELECT agent, event_type, payload, created_at FROM agent_traces WHERE research_id=? ORDER BY id",
                (research_id,),
            ).fetchall()
        out = []
        for r in rows:
            out.append(
                {
                    "agent": r["agent"],
                    "event_type": r["event_type"],
                    "payload": json.loads(r["payload"]),
                    "created_at": r["created_at"],
                }
            )
        return out

    def add_edge(self, src_type: str, src_id: str, rel: str, dst_type: str, dst_id: str, meta: dict | None = None) -> None:
        with self.conn() as c:
            c.execute(
                "INSERT INTO lineage_edges (src_type, src_id, rel, dst_type, dst_id, meta) VALUES (?,?,?,?,?,?)",
                (src_type, src_id, rel, dst_type, dst_id, json.dumps(meta or {})),
            )

    def lineage_for(self, node_id: str) -> list[dict[str, Any]]:
        with self.conn() as c:
            rows = c.execute(
                "SELECT * FROM lineage_edges WHERE src_id=? OR dst_id=? ORDER BY id",
                (node_id, node_id),
            ).fetchall()
        return [dict(r) for r in rows]

    def set_memory(self, key: str, kind: str, payload: dict[str, Any]) -> None:
        with self.conn() as c:
            c.execute(
                "INSERT INTO research_memory (key, kind, payload, updated_at) VALUES (?,?,?,?) "
                "ON CONFLICT(key) DO UPDATE SET kind=excluded.kind, payload=excluded.payload, updated_at=excluded.updated_at",
                (key, kind, json.dumps(payload), _utcnow()),
            )

    def get_memory(self, key: str) -> dict[str, Any] | None:
        with self.conn() as c:
            row = c.execute("SELECT payload FROM research_memory WHERE key=?", (key,)).fetchone()
        return json.loads(row["payload"]) if row else None

    def save_checkpoint(self, research_id: str, node: str, payload: dict[str, Any]) -> None:
        self.upsert_json(
            "research_checkpoints",
            "research_id",
            research_id,
            {"node": node, **payload},
            node=node,
            updated_at=_utcnow(),
        )

    def get_checkpoint(self, research_id: str) -> dict[str, Any] | None:
        return self.get_json("research_checkpoints", "research_id", research_id)

    def is_cancelled(self, research_id: str) -> bool:
        raw = self.get_json("research_requests", "research_id", research_id)
        return bool(raw and raw.get("status") == "CANCELLED")

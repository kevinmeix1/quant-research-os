"""Reproducibility hashing."""

from __future__ import annotations

import hashlib
import json
import subprocess
from typing import Any


def stable_json(obj: Any) -> str:
    return json.dumps(obj, sort_keys=True, default=str, separators=(",", ":"))


def configuration_hash(config: dict[str, Any]) -> str:
    return hashlib.sha256(stable_json(config).encode()).hexdigest()[:16]


def code_commit() -> str | None:
    try:
        out = subprocess.check_output(
            ["git", "rev-parse", "--short", "HEAD"],
            stderr=subprocess.DEVNULL,
            text=True,
        ).strip()
        return out or None
    except Exception:
        return None

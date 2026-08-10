"""Filesystem layout for local research artifacts."""

from __future__ import annotations

import os
from pathlib import Path


def project_root() -> Path:
    return Path(__file__).resolve().parents[3]


def data_root() -> Path:
    env = os.environ.get("QROS_DATA_ROOT")
    root = Path(env) if env else project_root() / "data" / "local"
    root.mkdir(parents=True, exist_ok=True)
    return root


def db_path() -> Path:
    p = data_root() / "qros.sqlite"
    p.parent.mkdir(parents=True, exist_ok=True)
    return p


def artifacts_dir(*parts: str) -> Path:
    p = data_root() / "artifacts"
    for part in parts:
        p = p / part
    p.mkdir(parents=True, exist_ok=True)
    return p

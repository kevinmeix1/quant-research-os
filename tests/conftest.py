from __future__ import annotations

import os

import pytest


@pytest.fixture()
def tmp_db(tmp_path, monkeypatch):
    monkeypatch.setenv("QROS_DATA_ROOT", str(tmp_path / "qros_data"))
    from quant_research_os.storage.db import ResearchDB

    return ResearchDB()

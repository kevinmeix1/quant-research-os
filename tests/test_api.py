from __future__ import annotations

from fastapi.testclient import TestClient


def test_api_health_and_research(tmp_db, monkeypatch):
    monkeypatch.setenv("QROS_DATA_ROOT", str(tmp_db.path.parent))
    import importlib
    import quant_research_os.api.app as api_mod
    import quant_research_os.storage.db as db_mod
    import quant_research_os.storage.paths as paths_mod

    monkeypatch.delenv("QROS_API_KEY", raising=False)
    importlib.reload(paths_mod)
    importlib.reload(db_mod)
    importlib.reload(api_mod)

    client = TestClient(api_mod.app)
    assert client.get("/health").json()["status"] == "ok"
    resp = client.post(
        "/research",
        json={
            "question": "Find a robust cross-sectional FX strategy with low correlation to momentum.",
            "universe": "FX_G10",
            "max_experiments": 10,
            "max_hypotheses": 1,
        },
    )
    assert resp.status_code == 200
    body = resp.json()
    assert "research_id" in body
    assert "decision" in body
    assert client.get(f"/research/{body['research_id']}/trace").status_code == 200
    assert client.get("/alphas").status_code == 200
    assert client.get("/experiments").status_code == 200
    assert client.get("/portfolio").status_code == 200
    assert client.get("/").status_code == 200

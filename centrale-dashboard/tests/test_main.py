import json

from fastapi.testclient import TestClient

from centrale_dashboard import config


def _client(monkeypatch, tmp_path, **overrides):
    """Fresh app import per test so module-level config reads pick up
    monkeypatched env values instead of whatever was set at import time."""
    monkeypatch.setattr(config, "FLOWSINT_API_URL", overrides.get("flowsint_api_url"))
    monkeypatch.setattr(config, "FLOWSINT_USERNAME", overrides.get("flowsint_username"))
    monkeypatch.setattr(config, "FLOWSINT_PASSWORD", overrides.get("flowsint_password"))
    monkeypatch.setattr(
        config, "FORENSICS_SOURCES", overrides.get("forensics_sources", "")
    )
    monkeypatch.setattr(
        config, "PENTEST_REPORTS_DIR", overrides.get("pentest_reports_dir")
    )
    monkeypatch.setattr(
        config,
        "BLUETEAM_PIVOT_FILE",
        overrides.get("blueteam_pivot_file", str(tmp_path / "missing.jsonl")),
    )

    from centrale_dashboard.main import app

    return TestClient(app)


def test_status_reflects_unconfigured_sources(monkeypatch, tmp_path):
    client = _client(monkeypatch, tmp_path)
    body = client.get("/api/status").json()
    assert body == {
        "osint_configured": False,
        "forensics_configured": False,
        "pentest_configured": False,
        "blueteam_configured": False,
    }


def test_osint_endpoint_not_configured(monkeypatch, tmp_path):
    client = _client(monkeypatch, tmp_path)
    body = client.get("/api/osint/investigations").json()
    assert body == {"configured": False, "investigations": []}


def test_forensics_endpoint_lists_cases(monkeypatch, tmp_path):
    cases_root = tmp_path / "iped_cases"
    (cases_root / "case1").mkdir(parents=True)
    (cases_root / "case1" / "chain_of_custody.log").write_text(
        "[t] ACQUISITION START source='s' label='exhibit-01' operator='alice' host='h'\n"
        "[t] INTEGRITY OK - source and image hashes match\n"
        "[t] ACQUISITION END image='x'\n"
    )
    client = _client(monkeypatch, tmp_path, forensics_sources=f"IPED={cases_root}")

    body = client.get("/api/forensics/cases").json()

    assert body["configured"] is True
    assert body["cases"][0]["status"] == "verified"
    assert body["cases"][0]["tool"] == "IPED"


def test_pentest_endpoint_not_configured(monkeypatch, tmp_path):
    client = _client(monkeypatch, tmp_path)
    body = client.get("/api/pentest/reports").json()
    assert body == {"configured": False, "reports": []}


def test_blueteam_endpoint_reads_pivot_file(monkeypatch, tmp_path):
    pivot_file = tmp_path / "pivots.jsonl"
    pivot_file.write_text(json.dumps({"ip": "9.9.9.9", "severity": "critical"}) + "\n")
    client = _client(monkeypatch, tmp_path, blueteam_pivot_file=str(pivot_file))

    body = client.get("/api/blueteam/pivots").json()

    assert body["configured"] is True
    assert body["pivots"][0]["ip"] == "9.9.9.9"


def test_frontend_is_served(monkeypatch, tmp_path):
    client = _client(monkeypatch, tmp_path)
    resp = client.get("/")
    assert resp.status_code == 200
    assert "Centrale" in resp.text

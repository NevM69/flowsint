from centrale_dashboard.sources.osint import summarize_investigations


def test_summarize_maps_fields():
    raw = [
        {
            "name": "Dossier X",
            "status": "active",
            "sketches": [{"id": "1"}, {"id": "2"}],
            "current_user_role": "OWNER",
            "last_updated_at": "2026-07-30T10:00:00Z",
        }
    ]
    rows = summarize_investigations(raw)
    assert rows == [
        {
            "name": "Dossier X",
            "status": "active",
            "sketches": 2,
            "role": "OWNER",
            "last_updated_at": "2026-07-30T10:00:00Z",
        }
    ]


def test_summarize_handles_missing_sketches():
    raw = [
        {
            "name": "Dossier Y",
            "status": "closed",
            "current_user_role": None,
            "last_updated_at": None,
        }
    ]
    rows = summarize_investigations(raw)
    assert rows[0]["sketches"] == 0


def test_summarize_empty_list():
    assert summarize_investigations([]) == []

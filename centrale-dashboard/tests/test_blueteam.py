import json

from centrale_dashboard.sources.blueteam import list_pivots


class TestListPivots:
    def test_reads_jsonl_newest_first(self, tmp_path):
        pivot_file = tmp_path / "pivots.jsonl"
        records = [
            {
                "ip": "1.1.1.1",
                "severity": "warning",
                "alert_type": "beacon",
                "message": "m1",
                "timestamp": "t1",
            },
            {
                "ip": "2.2.2.2",
                "severity": "critical",
                "alert_type": "exfil",
                "message": "m2",
                "timestamp": "t2",
            },
        ]
        pivot_file.write_text("\n".join(json.dumps(r) for r in records) + "\n")

        pivots = list_pivots(pivot_file)

        assert [p["ip"] for p in pivots] == ["2.2.2.2", "1.1.1.1"]

    def test_missing_file(self, tmp_path):
        assert list_pivots(tmp_path / "does-not-exist.jsonl") == []

    def test_skips_malformed_lines(self, tmp_path):
        pivot_file = tmp_path / "pivots.jsonl"
        pivot_file.write_text('{"ip": "1.1.1.1"}\n{not valid json\n{"ip": "2.2.2.2"}\n')

        pivots = list_pivots(pivot_file)

        assert [p["ip"] for p in pivots] == ["2.2.2.2", "1.1.1.1"]

    def test_respects_limit(self, tmp_path):
        pivot_file = tmp_path / "pivots.jsonl"
        pivot_file.write_text(
            "\n".join(json.dumps({"ip": f"1.1.1.{i}"}) for i in range(10)) + "\n"
        )

        pivots = list_pivots(pivot_file, limit=3)

        assert len(pivots) == 3

    def test_ignores_blank_lines(self, tmp_path):
        pivot_file = tmp_path / "pivots.jsonl"
        pivot_file.write_text('{"ip": "1.1.1.1"}\n\n\n{"ip": "2.2.2.2"}\n')

        assert len(list_pivots(pivot_file)) == 2

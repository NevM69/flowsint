from pathlib import Path

from centrale_dashboard.sources.forensics import (
    list_cases,
    parse_custody_log,
    parse_sources_env,
)

# Real acquire_and_hash.sh output lines run long - excluded from the E501
# line-length check for this file rather than reflowed, so the fixture stays
# a faithful copy-paste of what the script actually produces.
VERIFIED_LOG = """\
[2026-07-30T06:59:52Z] ACQUISITION START source='fake_evidence.bin' label='exhibit-01' operator='root' host='vm'
[2026-07-30T06:59:52Z] SOURCE SHA256 (pre-copy)  = abc
[2026-07-30T06:59:52Z] SOURCE SHA256 (post-copy) = abc
[2026-07-30T06:59:52Z] IMAGE  SHA256             = abc
[2026-07-30T06:59:52Z] INTEGRITY OK - source and image hashes match
[2026-07-30T06:59:52Z] ACQUISITION END image='./case1/exhibit-01.dd'
"""

FAILED_LOG = """\
[2026-07-30T07:00:33Z] ACQUISITION START source='fake_evidence2.bin' label='exhibit-02' operator='root' host='vm'
[2026-07-30T07:00:33Z] INTEGRITY FAIL - image hash does not match source hash
"""


class TestParseSourcesEnv:
    def test_parses_multiple_pairs(self):
        assert parse_sources_env("IPED=/a/cases,Autopsy=/b/cases") == [
            ("IPED", Path("/a/cases")),
            ("Autopsy", Path("/b/cases")),
        ]

    def test_empty_or_none(self):
        assert parse_sources_env(None) == []
        assert parse_sources_env("") == []

    def test_skips_malformed_entries(self):
        assert parse_sources_env("IPED=/a/cases,garbage,=/no-label,NoPath=") == [
            ("IPED", Path("/a/cases"))
        ]

    def test_strips_whitespace(self):
        assert parse_sources_env(" IPED = /a/cases , Autopsy=/b/cases ") == [
            ("IPED", Path("/a/cases")),
            ("Autopsy", Path("/b/cases")),
        ]


class TestParseCustodyLog:
    def test_verified(self):
        result = parse_custody_log(VERIFIED_LOG)
        assert result["status"] == "verified"
        assert result["evidence_label"] == "exhibit-01"
        assert result["operator"] == "root"
        assert result["started_at"] == "2026-07-30T06:59:52Z"

    def test_integrity_failed(self):
        result = parse_custody_log(FAILED_LOG)
        assert result["status"] == "integrity_failed"

    def test_in_progress(self):
        log = "[2026-07-30T00:00:00Z] ACQUISITION START source='x' label='exhibit-03' operator='a' host='h'\n"
        assert parse_custody_log(log)["status"] == "in_progress"

    def test_unknown_for_empty_log(self):
        assert parse_custody_log("")["status"] == "unknown"


class TestListCases:
    def test_lists_cases_across_multiple_sources(self, tmp_path):
        iped_cases = tmp_path / "iped_cases"
        autopsy_cases = tmp_path / "autopsy_cases"
        (iped_cases / "case1").mkdir(parents=True)
        (iped_cases / "case1" / "chain_of_custody.log").write_text(VERIFIED_LOG)
        (autopsy_cases / "case2").mkdir(parents=True)
        (autopsy_cases / "case2" / "chain_of_custody.log").write_text(FAILED_LOG)

        cases = list_cases([("IPED", iped_cases), ("Autopsy", autopsy_cases)])

        assert len(cases) == 2
        assert {c["tool"] for c in cases} == {"IPED", "Autopsy"}
        by_tool = {c["tool"]: c for c in cases}
        assert by_tool["IPED"]["status"] == "verified"
        assert by_tool["Autopsy"]["status"] == "integrity_failed"

    def test_case_without_custody_log(self, tmp_path):
        cases_root = tmp_path / "cases"
        (cases_root / "case-no-log").mkdir(parents=True)

        cases = list_cases([("IPED", cases_root)])

        assert cases[0]["status"] == "no_custody_log"

    def test_nonexistent_source_dir_is_skipped(self, tmp_path):
        assert list_cases([("IPED", tmp_path / "does-not-exist")]) == []

    def test_ignores_non_directory_entries(self, tmp_path):
        cases_root = tmp_path / "cases"
        cases_root.mkdir()
        (cases_root / "stray-file.txt").write_text("not a case")

        assert list_cases([("IPED", cases_root)]) == []

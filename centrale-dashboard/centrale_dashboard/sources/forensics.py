"""Forensics tab: reads case status from IPED/autopsy chain_of_custody.log
files, written by each repo's docker/acquire_and_hash.sh."""

import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple


def parse_sources_env(value: Optional[str]) -> List[Tuple[str, Path]]:
    """Parse "Label=/path,Label2=/path2" into [(label, Path), ...].
    Blank or malformed entries are skipped rather than raising, so one typo
    doesn't take the whole tab down."""
    if not value:
        return []
    sources = []
    for entry in value.split(","):
        entry = entry.strip()
        if not entry or "=" not in entry:
            continue
        label, _, path = entry.partition("=")
        label, path = label.strip(), path.strip()
        if label and path:
            sources.append((label, Path(path)))
    return sources


def parse_custody_log(text: str) -> Dict[str, Optional[str]]:
    started = "ACQUISITION START" in text
    ended = "ACQUISITION END" in text
    failed = "INTEGRITY FAIL" in text
    verified = "INTEGRITY OK" in text

    if failed:
        status = "integrity_failed"
    elif verified and ended:
        status = "verified"
    elif started and not ended:
        status = "in_progress"
    else:
        status = "unknown"

    label_match = re.search(r"label='([^']*)'", text)
    operator_match = re.search(r"operator='([^']*)'", text)
    first_ts_match = re.search(r"^\[([^\]]+)\]", text, re.MULTILINE)

    return {
        "status": status,
        "evidence_label": label_match.group(1) if label_match else None,
        "operator": operator_match.group(1) if operator_match else None,
        "started_at": first_ts_match.group(1) if first_ts_match else None,
    }


def list_cases(sources: List[Tuple[str, Path]]) -> List[Dict[str, Optional[str]]]:
    cases = []
    for tool_label, cases_root in sources:
        if not cases_root.exists():
            continue
        for case_dir in sorted(cases_root.iterdir()):
            if not case_dir.is_dir():
                continue
            entry: Dict[str, Optional[str]] = {
                "tool": tool_label,
                "case": case_dir.name,
                "status": "no_custody_log",
                "evidence_label": None,
                "operator": None,
                "started_at": None,
            }
            log_path = case_dir / "chain_of_custody.log"
            if log_path.exists():
                entry.update(parse_custody_log(log_path.read_text()))
            cases.append(entry)
    return cases

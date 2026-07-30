"""Blue-team tab: reads the JSONL pivot queue written by
pcybox-orbis/blueteam/export_pivots.py."""

import json
from pathlib import Path
from typing import Any, Dict, List


def list_pivots(pivot_file: Path, limit: int = 50) -> List[Dict[str, Any]]:
    if not pivot_file.exists():
        return []
    pivots = []
    for line in pivot_file.read_text().splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            pivots.append(json.loads(line))
        except json.JSONDecodeError:
            # A partially-written last line (e.g. read mid-append) shouldn't
            # take down every other pivot in the file.
            continue
    pivots.reverse()  # newest first
    return pivots[:limit]

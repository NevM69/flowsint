import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

# OSINT tab: talks to a running flowsint-api instance over its existing
# /auth/token + /investigations endpoints. Unset -> tab shows "not configured"
# instead of erroring.
FLOWSINT_API_URL = os.environ.get("FLOWSINT_API_URL", "").rstrip("/") or None
FLOWSINT_USERNAME = os.environ.get("FLOWSINT_USERNAME")
FLOWSINT_PASSWORD = os.environ.get("FLOWSINT_PASSWORD")

# Forensics tab: "Label=/path/to/cases,Label2=/path/to/other/cases" - each
# case's chain_of_custody.log (written by IPED/autopsy's
# docker/acquire_and_hash.sh) is what gets parsed for status.
FORENSICS_SOURCES = os.environ.get("FORENSICS_SOURCES", "")

# Pentest tab: root of an Awesome-Pentest lab/reports/ directory.
PENTEST_REPORTS_DIR = os.environ.get("PENTEST_REPORTS_DIR")

# Blue-team tab: the JSONL pivot queue written by
# pcybox-orbis/blueteam/export_pivots.py.
BLUETEAM_PIVOT_FILE = os.environ.get(
    "BLUETEAM_PIVOT_FILE", str(Path.home() / ".pcybox-orbis" / "pivot_queue.jsonl")
)

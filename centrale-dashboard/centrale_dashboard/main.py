from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from . import config
from .sources import blueteam, forensics, osint, pentest

app = FastAPI(title="Centrale Dashboard")

STATIC_DIR = Path(__file__).parent.parent / "static"


@app.get("/api/status")
def get_status() -> dict:
    forensics_sources = forensics.parse_sources_env(config.FORENSICS_SOURCES)
    return {
        "osint_configured": bool(config.FLOWSINT_API_URL),
        "forensics_configured": bool(forensics_sources),
        "pentest_configured": bool(config.PENTEST_REPORTS_DIR),
        "blueteam_configured": Path(config.BLUETEAM_PIVOT_FILE).exists(),
    }


@app.get("/api/osint/investigations")
def get_osint() -> dict:
    if not (
        config.FLOWSINT_API_URL
        and config.FLOWSINT_USERNAME
        and config.FLOWSINT_PASSWORD
    ):
        return {"configured": False, "investigations": []}
    try:
        raw = osint.fetch_investigations(
            config.FLOWSINT_API_URL, config.FLOWSINT_USERNAME, config.FLOWSINT_PASSWORD
        )
        return {
            "configured": True,
            "investigations": osint.summarize_investigations(raw),
        }
    except Exception as e:
        return {"configured": True, "error": str(e), "investigations": []}


@app.get("/api/forensics/cases")
def get_forensics() -> dict:
    sources = forensics.parse_sources_env(config.FORENSICS_SOURCES)
    if not sources:
        return {"configured": False, "cases": []}
    return {"configured": True, "cases": forensics.list_cases(sources)}


@app.get("/api/pentest/reports")
def get_pentest() -> dict:
    if not config.PENTEST_REPORTS_DIR:
        return {"configured": False, "reports": []}
    return {
        "configured": True,
        "reports": pentest.list_reports(Path(config.PENTEST_REPORTS_DIR)),
    }


@app.get("/api/blueteam/pivots")
def get_blueteam() -> dict:
    pivot_file = Path(config.BLUETEAM_PIVOT_FILE)
    return {
        "configured": pivot_file.exists(),
        "pivots": blueteam.list_pivots(pivot_file),
    }


# Serve the static frontend last so it doesn't shadow the /api/* routes above.
app.mount("/", StaticFiles(directory=str(STATIC_DIR), html=True), name="static")

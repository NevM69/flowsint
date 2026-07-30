"""OSINT tab: reads investigations from a running flowsint-api instance."""

from typing import Any, Dict, List, Optional

import requests


def get_token(base_url: str, username: str, password: str) -> str:
    resp = requests.post(
        f"{base_url}/auth/token",
        data={"username": username, "password": password},
        timeout=10,
    )
    resp.raise_for_status()
    return resp.json()["access_token"]


def fetch_investigations(
    base_url: str, username: str, password: str
) -> List[Dict[str, Any]]:
    token = get_token(base_url, username, password)
    resp = requests.get(
        f"{base_url}/investigations",
        headers={"Authorization": f"Bearer {token}"},
        timeout=10,
    )
    resp.raise_for_status()
    return resp.json()


def summarize_investigations(
    investigations: List[Dict[str, Any]],
) -> List[Dict[str, Optional[Any]]]:
    """Raw /investigations response -> flat rows the dashboard table renders."""
    return [
        {
            "name": inv.get("name"),
            "status": inv.get("status"),
            "sketches": len(inv.get("sketches") or []),
            "role": inv.get("current_user_role"),
            "last_updated_at": inv.get("last_updated_at"),
        }
        for inv in investigations
    ]

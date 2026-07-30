from typing import Any, Dict, List

import requests

from ..base import Tool


class PappersTool(Tool):
    """Wraps the Pappers API v2 (French company registry, financials, beneficial owners)."""

    BASE_URL = "https://api.pappers.fr/v2"

    def __init__(self, api_token: str):
        self.api_token = api_token

    @classmethod
    def name(cls) -> str:
        return "pappers"

    @classmethod
    def version(cls) -> str:
        return "2.0.0"

    @classmethod
    def description(cls) -> str:
        return "The Pappers API provides legal, financial, and beneficial ownership data for French companies."

    @classmethod
    def category(cls) -> str:
        return "Business intelligence"

    def launch(self, siren: str) -> Dict[str, Any]:
        return self.get_entreprise(siren)

    def get_entreprise(self, siren: str) -> Dict[str, Any]:
        try:
            resp = requests.get(
                f"{self.BASE_URL}/entreprise",
                params={"api_token": self.api_token, "siren": siren},
                timeout=15,
            )
            resp.raise_for_status()
            return resp.json()
        except requests.HTTPError as e:
            output = getattr(e.response, "text", "No output")
            raise RuntimeError(
                f"Pappers API returned an error for SIREN {siren}: {e}. Output: {output}"
            )
        except Exception as e:
            raise RuntimeError(
                f"Error querying Pappers API for SIREN {siren}: {str(e)}"
            )

    def search_entreprise(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        try:
            resp = requests.get(
                f"{self.BASE_URL}/recherche",
                params={"api_token": self.api_token, "q": query, "par_page": limit},
                timeout=15,
            )
            resp.raise_for_status()
            data = resp.json()
            return data.get("resultats", [])
        except Exception as e:
            raise RuntimeError(f"Error searching Pappers API for '{query}': {str(e)}")

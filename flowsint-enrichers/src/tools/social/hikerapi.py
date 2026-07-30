from typing import Any, Dict

import requests

from ..base import Tool


class HikerAPITool(Tool):
    """Wraps HikerAPI (https://hikerapi.com), the Instagram data API used by Osintgram2."""

    BASE_URL = "https://api.hikerapi.com"

    def __init__(self, access_key: str):
        self.access_key = access_key

    @classmethod
    def name(cls) -> str:
        return "hikerapi"

    @classmethod
    def version(cls) -> str:
        return "2.0.0"

    @classmethod
    def description(cls) -> str:
        return "HikerAPI provides read access to public Instagram profile data (used by Osintgram)."

    @classmethod
    def category(cls) -> str:
        return "Social intelligence"

    def launch(self, username: str) -> Dict[str, Any]:
        return self.get_user_by_username(username)

    def get_user_by_username(self, username: str) -> Dict[str, Any]:
        try:
            resp = requests.get(
                f"{self.BASE_URL}/v2/user/by/username",
                params={"username": username},
                headers={"x-access-key": self.access_key},
                timeout=15,
            )
            resp.raise_for_status()
            return resp.json()
        except requests.HTTPError as e:
            output = getattr(e.response, "text", "No output")
            raise RuntimeError(
                f"HikerAPI returned an error for username '{username}': {e}. Output: {output}"
            )
        except Exception as e:
            raise RuntimeError(
                f"Error querying HikerAPI for username '{username}': {str(e)}"
            )

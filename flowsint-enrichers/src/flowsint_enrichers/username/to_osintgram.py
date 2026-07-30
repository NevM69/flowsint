from typing import Any, Dict, List, Optional

from flowsint_core.core.enricher_base import Enricher
from flowsint_core.core.logger import Logger
from flowsint_enrichers.registry import flowsint_enricher
from flowsint_types.email import Email
from flowsint_types.phone import Phone
from flowsint_types.social_account import SocialAccount
from flowsint_types.username import Username
from tools.social.hikerapi import HikerAPITool


@flowsint_enricher
class UsernameToOsintgram(Enricher):
    """[Osintgram] Get an Instagram profile (bio, follower counts, public contact info) for a username, via HikerAPI."""

    InputType = Username
    OutputType = SocialAccount

    def __init__(
        self,
        sketch_id: Optional[str] = None,
        scan_id: Optional[str] = None,
        vault=None,
        params: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(
            sketch_id=sketch_id,
            scan_id=scan_id,
            params_schema=self.get_params_schema(),
            vault=vault,
            params=params,
        )

    @classmethod
    def get_params_schema(cls) -> List[Dict[str, Any]]:
        return [
            {
                "name": "HIKERAPI_TOKEN",  # Get your token from https://hikerapi.com/tokens
                "type": "vaultSecret",
                "description": "Your HikerAPI access token (used by Osintgram to read Instagram data).",
                "required": True,
            }
        ]

    @classmethod
    def name(cls) -> str:
        return "username_to_instagram"

    @classmethod
    def category(cls) -> str:
        return "social"

    @classmethod
    def key(cls) -> str:
        return "username"

    async def scan(self, data: List[InputType]) -> List[OutputType]:
        results: List[OutputType] = []
        access_key = self.get_secret("HIKERAPI_TOKEN")
        hiker = HikerAPITool(access_key=access_key)

        for username in data:
            try:
                profile = hiker.get_user_by_username(username.value)
                if not profile or profile.get("pk") is None:
                    Logger.error(
                        self.sketch_id,
                        {
                            "message": f"(UsernameToOsintgram) No Instagram profile found for '{username.value}'."
                        },
                    )
                    continue

                results.append(self.build_social_account(username, profile))
            except Exception as e:
                Logger.error(
                    self.sketch_id,
                    {
                        "message": f"(UsernameToOsintgram) Error fetching Instagram profile for '{username.value}': {e}"
                    },
                )

        return results

    def build_social_account(
        self, username: Username, profile: Dict[str, Any]
    ) -> SocialAccount:
        associated_emails = []
        if profile.get("public_email"):
            try:
                associated_emails.append(Email(email=profile["public_email"]).email)
            except Exception:
                pass

        associated_phones = []
        if profile.get("public_phone_number"):
            try:
                number = profile.get("public_phone_number")
                if profile.get("public_phone_country_code"):
                    number = f"+{profile['public_phone_country_code']}{number}"
                associated_phones.append(Phone(number=number).number)
            except Exception:
                pass

        return SocialAccount(
            username=username,
            platform="instagram",
            display_name=profile.get("full_name"),
            profile_url=f"https://instagram.com/{username.value}",
            profile_picture_url=profile.get("profile_pic_url"),
            bio=profile.get("biography"),
            followers_count=profile.get("follower_count"),
            following_count=profile.get("following_count"),
            posts_count=profile.get("media_count"),
            verified=profile.get("is_verified"),
            is_private=profile.get("is_private"),
            associated_emails=associated_emails or None,
            associated_phones=associated_phones or None,
        )

    def postprocess(
        self, results: List[OutputType], input_data: List[InputType] = None
    ) -> List[OutputType]:
        if not self._graph_service:
            return results

        for social_account in results:
            username_value = social_account.username.value
            try:
                self.create_node(social_account.username)
                self.create_node(social_account)
                self.create_relationship(
                    social_account.username, social_account, "HAS_SOCIAL_ACCOUNT"
                )
                self.log_graph_message(f"{username_value} -> Instagram profile found")

                for email in social_account.associated_emails or []:
                    email_obj = Email(email=email)
                    self.create_node(email_obj)
                    self.create_relationship(social_account, email_obj, "HAS_EMAIL")

                for phone in social_account.associated_phones or []:
                    phone_obj = Phone(number=phone)
                    self.create_node(phone_obj)
                    self.create_relationship(social_account, phone_obj, "HAS_PHONE")
            except Exception as e:
                Logger.error(
                    self.sketch_id,
                    {
                        "message": f"(UsernameToOsintgram) Failed to create graph nodes for '{username_value}': {e}"
                    },
                )
                continue

        return results


InputType = UsernameToOsintgram.InputType
OutputType = UsernameToOsintgram.OutputType

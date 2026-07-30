from flowsint_enrichers.username.to_osintgram import UsernameToOsintgram
from flowsint_types.username import Username

HIKERAPI_PROFILE = {
    "pk": "123456789",
    "username": "janedoe",
    "full_name": "Jane Doe",
    "is_private": False,
    "is_verified": True,
    "profile_pic_url": "https://example.com/pic.jpg",
    "biography": "OSINT enthusiast",
    "follower_count": 1000,
    "following_count": 200,
    "media_count": 42,
    "public_email": "jane@example.com",
    "public_phone_number": "612345678",
    "public_phone_country_code": "33",
}


def make_enricher() -> UsernameToOsintgram:
    return UsernameToOsintgram(sketch_id="test-sketch", scan_id="test-scan")


def test_name_category_key():
    enricher = make_enricher()
    assert enricher.name() == "username_to_instagram"
    assert enricher.category() == "social"
    assert enricher.key() == "username"


def test_build_social_account_maps_profile_fields():
    enricher = make_enricher()
    username = Username(value="janedoe")

    account = enricher.build_social_account(username, HIKERAPI_PROFILE)

    assert account.platform == "instagram"
    assert account.display_name == "Jane Doe"
    assert account.profile_url == "https://instagram.com/janedoe"
    assert account.followers_count == 1000
    assert account.verified is True
    assert account.is_private is False
    assert account.associated_emails == ["jane@example.com"]
    assert account.associated_phones == ["+33612345678"]


def test_build_social_account_without_public_contact_info():
    enricher = make_enricher()
    username = Username(value="janedoe")
    profile = {k: v for k, v in HIKERAPI_PROFILE.items() if not k.startswith("public_")}

    account = enricher.build_social_account(username, profile)

    assert account.associated_emails is None
    assert account.associated_phones is None

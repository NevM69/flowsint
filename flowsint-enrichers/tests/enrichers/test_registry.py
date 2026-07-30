import pytest
from flowsint_enrichers import ENRICHER_REGISTRY


def test_enricher_registry_enricher_found():
    enricher = ENRICHER_REGISTRY.get_enricher("domain_to_ip", "123", "123")
    assert enricher.name() == "domain_to_ip"


def test_enricher_registry_enricher_not_found():
    with pytest.raises(Exception) as error:
        ENRICHER_REGISTRY.get_enricher("enricher_does_not_exist", "123", "123")
        assert "not found" in str(error.value)


def test_enricher_registry_org_to_pappers_found():
    enricher = ENRICHER_REGISTRY.get_enricher("org_to_pappers", "123", "123")
    assert enricher.name() == "org_to_pappers"


def test_enricher_registry_username_to_instagram_found():
    enricher = ENRICHER_REGISTRY.get_enricher("username_to_instagram", "123", "123")
    assert enricher.name() == "username_to_instagram"


def test_enricher_registry_website_to_torbot_found():
    enricher = ENRICHER_REGISTRY.get_enricher("website_to_torbot", "123", "123")
    assert enricher.name() == "website_to_torbot"

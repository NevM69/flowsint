from flowsint_enrichers.website.to_torbot import WebsiteToTorbot


def make_enricher() -> WebsiteToTorbot:
    return WebsiteToTorbot(sketch_id="test-sketch", scan_id="test-scan")


def test_name_category_key():
    enricher = make_enricher()
    assert enricher.name() == "website_to_torbot"
    assert enricher.category() == "Website"
    assert enricher.key() == "url"


def test_no_vault_secret_required():
    """Unlike Pappers/Osintgram, Tor access needs no API key."""
    enricher = make_enricher()
    assert all(param["type"] != "vaultSecret" for param in enricher.get_params_schema())


def test_default_params():
    enricher = make_enricher()
    defaults = {p["name"]: p.get("default") for p in enricher.get_params_schema()}
    assert defaults["use_tor"] == "true"
    assert defaults["socks_host"] == "127.0.0.1"
    assert defaults["socks_port"] == "9050"
    assert defaults["max_links"] == "15"

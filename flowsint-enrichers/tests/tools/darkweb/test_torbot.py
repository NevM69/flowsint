import phonenumbers
from bs4 import BeautifulSoup

from tools.darkweb.tor_crawler import TorCrawlerTool

tool = TorCrawlerTool()


def test_name():
    assert tool.name() == "torbot"


def test_category():
    assert tool.category() == "Dark web intelligence"


def test_extract_links_resolves_relative_and_dedupes():
    html = """
    <a href="http://example.onion/page1">1</a>
    <a href="/page2">2</a>
    <a href="page2">2 again</a>
    <a href="javascript:void(0)">skip</a>
    <a href="mailto:test@example.onion">skip</a>
    <a href="#anchor">skip</a>
    """
    soup = BeautifulSoup(html, "html.parser")
    links = tool._extract_links(soup, "http://example.onion/")

    assert links == ["http://example.onion/page1", "http://example.onion/page2"]


def test_extract_emails():
    text = "Contact us at admin@example.onion or sales@example.onion for more info."
    emails = tool._extract_emails(text)

    assert emails == ["admin@example.onion", "sales@example.onion"]


def test_extract_phones():
    example = phonenumbers.example_number("US")
    formatted = phonenumbers.format_number(
        example, phonenumbers.PhoneNumberFormat.INTERNATIONAL
    )
    expected = phonenumbers.format_number(example, phonenumbers.PhoneNumberFormat.E164)
    text = f"Call us at {formatted} for questions."

    phones = tool._extract_phones(text)

    assert phones == [expected]

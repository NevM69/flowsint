import re
from typing import Any, Dict, List
from urllib.parse import urljoin, urlparse

import phonenumbers
import requests
from bs4 import BeautifulSoup

from ..base import Tool

EMAIL_PATTERN = re.compile(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}")


class TorCrawlerTool(Tool):
    """Single-page fetcher/parser for the Tor network, in the spirit of TorBot
    (https://github.com/DedSecInside/TorBot). Reimplemented against `requests` +
    PySocks instead of depending on the `torbot` package directly, which pulls in
    scikit-learn/scipy/igraph/pyinstaller for a handful of parsing helpers.
    """

    @classmethod
    def name(cls) -> str:
        return "torbot"

    @classmethod
    def version(cls) -> str:
        return "1.0.0"

    @classmethod
    def description(cls) -> str:
        return "Crawls a single page over the Tor network (or clearnet) and extracts links, emails, and phone numbers."

    @classmethod
    def category(cls) -> str:
        return "Dark web intelligence"

    def launch(
        self,
        url: str,
        use_tor: bool = True,
        socks_host: str = "127.0.0.1",
        socks_port: int = 9050,
        timeout: int = 30,
    ) -> Dict[str, Any]:
        proxies = None
        if use_tor:
            proxy_url = f"socks5h://{socks_host}:{socks_port}"
            proxies = {"http": proxy_url, "https": proxy_url}

        try:
            resp = requests.get(url, proxies=proxies, timeout=timeout)
        except Exception as e:
            raise RuntimeError(f"Failed to fetch {url} over Tor: {str(e)}")

        soup = BeautifulSoup(resp.text, "html.parser")
        title = (
            soup.title.text.strip()
            if soup.title and soup.title.text
            else urlparse(url).netloc
        )

        links = self._extract_links(soup, url)
        emails = self._extract_emails(resp.text)
        phones = self._extract_phones(resp.text)

        return {
            "url": url,
            "title": title,
            "status_code": resp.status_code,
            "links": links,
            "emails": emails,
            "phones": phones,
        }

    def _extract_links(self, soup: BeautifulSoup, base_url: str) -> List[str]:
        links = set()
        for tag in soup.find_all("a", href=True):
            href = tag["href"].strip()
            if not href or href.startswith(("javascript:", "mailto:", "#")):
                continue
            absolute = urljoin(base_url, href)
            parsed = urlparse(absolute)
            if parsed.scheme in ("http", "https") and parsed.netloc:
                links.add(absolute)
        return sorted(links)

    def _extract_emails(self, text: str) -> List[str]:
        return sorted(set(EMAIL_PATTERN.findall(text)))

    def _extract_phones(self, text: str) -> List[str]:
        numbers = set()
        for match in phonenumbers.PhoneNumberMatcher(text, "US"):
            numbers.add(
                phonenumbers.format_number(
                    match.number, phonenumbers.PhoneNumberFormat.E164
                )
            )
        return sorted(numbers)

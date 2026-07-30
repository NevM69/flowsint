from typing import Any, Dict, List, Optional, Tuple

from flowsint_core.core.enricher_base import Enricher
from flowsint_core.core.logger import Logger
from flowsint_enrichers.registry import flowsint_enricher
from flowsint_types.email import Email
from flowsint_types.phone import Phone
from flowsint_types.website import Website
from tools.darkweb.tor_crawler import TorCrawlerTool


@flowsint_enricher
class WebsiteToTorbot(Enricher):
    """[TorBot] Crawl a .onion (or clearnet) page over Tor, discovering outbound links and public contact info."""

    InputType = Website
    OutputType = Website

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
        # scan() gathers page contacts and discovered link edges here; neither fits
        # cleanly on the Website OutputType, so postprocess() reads them back off self.
        self._page_contacts: Dict[str, Dict[str, List[str]]] = {}
        self._link_edges: List[Tuple[str, str]] = []

    @classmethod
    def get_params_schema(cls) -> List[Dict[str, Any]]:
        return [
            {
                "name": "use_tor",
                "type": "select",
                "description": "Route requests through the Tor SOCKS5 proxy (required for .onion addresses).",
                "required": False,
                "default": "true",
                "options": [
                    {"label": "Enabled", "value": "true"},
                    {"label": "Disabled", "value": "false"},
                ],
            },
            {
                "name": "socks_host",
                "type": "string",
                "description": "Tor SOCKS5 proxy host.",
                "required": False,
                "default": "127.0.0.1",
            },
            {
                "name": "socks_port",
                "type": "number",
                "description": "Tor SOCKS5 proxy port.",
                "required": False,
                "default": "9050",
            },
            {
                "name": "max_links",
                "type": "number",
                "description": "Maximum number of outbound links to follow one level deep.",
                "required": False,
                "default": "15",
            },
        ]

    @classmethod
    def name(cls) -> str:
        return "website_to_torbot"

    @classmethod
    def category(cls) -> str:
        return "Website"

    @classmethod
    def key(cls) -> str:
        return "url"

    async def scan(self, data: List[InputType]) -> List[OutputType]:
        results: List[OutputType] = []

        use_tor = self.params.get("use_tor", "true") == "true"
        socks_host = self.params.get("socks_host") or "127.0.0.1"
        socks_port = int(self.params.get("socks_port") or 9050)
        max_links = int(self.params.get("max_links") or 15)
        crawler = TorCrawlerTool()

        for website in data:
            root_url = str(website.url)
            try:
                root_page = crawler.launch(
                    root_url,
                    use_tor=use_tor,
                    socks_host=socks_host,
                    socks_port=socks_port,
                )
            except Exception as e:
                Logger.error(
                    self.sketch_id,
                    {"message": f"(WebsiteToTorbot) Failed to crawl {root_url}: {e}"},
                )
                continue

            root_website = website.model_copy(deep=True)
            root_website.title = root_page["title"]
            root_website.status_code = root_page["status_code"]
            root_website.active = 200 <= root_page["status_code"] < 400
            results.append(root_website)
            self._page_contacts[root_url] = {
                "emails": root_page["emails"],
                "phones": root_page["phones"],
            }

            Logger.info(
                self.sketch_id,
                {
                    "message": f"(WebsiteToTorbot) {root_url}: {len(root_page['links'])} links, "
                    f"{len(root_page['emails'])} emails, {len(root_page['phones'])} phones found."
                },
            )

            for link in root_page["links"][:max_links]:
                try:
                    child_page = crawler.launch(
                        link,
                        use_tor=use_tor,
                        socks_host=socks_host,
                        socks_port=socks_port,
                    )
                    results.append(
                        Website(
                            url=link,
                            title=child_page["title"],
                            status_code=child_page["status_code"],
                            active=200 <= child_page["status_code"] < 400,
                        )
                    )
                    self._page_contacts[link] = {
                        "emails": child_page["emails"],
                        "phones": child_page["phones"],
                    }
                    self._link_edges.append((root_url, link))
                except Exception as e:
                    Logger.error(
                        self.sketch_id,
                        {
                            "message": f"(WebsiteToTorbot) Failed to crawl linked page {link}: {e}"
                        },
                    )

        return results

    def postprocess(
        self, results: List[OutputType], input_data: List[InputType]
    ) -> List[OutputType]:
        if not self._graph_service:
            return results

        for website in results:
            self.create_node(website)

            contacts = self._page_contacts.get(str(website.url), {})
            for email_str in contacts.get("emails", []):
                try:
                    email_obj = Email(email=email_str)
                    self.create_node(email_obj)
                    self.create_relationship(website, email_obj, "HAS_EMAIL")
                except Exception as e:
                    Logger.warn(
                        self.sketch_id,
                        {
                            "message": f"(WebsiteToTorbot) Skipping invalid email '{email_str}': {e}"
                        },
                    )

            for phone_str in contacts.get("phones", []):
                try:
                    phone_obj = Phone(number=phone_str)
                    self.create_node(phone_obj)
                    self.create_relationship(website, phone_obj, "HAS_PHONE")
                except Exception as e:
                    Logger.warn(
                        self.sketch_id,
                        {
                            "message": f"(WebsiteToTorbot) Skipping invalid phone '{phone_str}': {e}"
                        },
                    )

        for root_url, link in self._link_edges:
            self.create_relationship(
                Website(url=root_url), Website(url=link), "LINKS_TO"
            )
            self.log_graph_message(f"{root_url}: LINKS_TO -> {link}")

        return results


InputType = WebsiteToTorbot.InputType
OutputType = WebsiteToTorbot.OutputType

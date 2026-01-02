# web/search.py

import requests
import logging
from bs4 import BeautifulSoup
from datetime import datetime
from typing import Optional
from utils.config import load_config

logger = logging.getLogger("web")
config = load_config()


class WebSearch:
    def __init__(self, timeout: int = 10):
        self.timeout = timeout
        self.headers = {
            "User-Agent": "Mozilla/5.0 (verysleepy-ai)"
        }

    def search(self, control: dict, query: str) -> Optional[str]:
        if not control.get("web_required"):
            return None

        if not config.get("web", {}).get("enabled", True):
            return None

        try:
            results = self._duckduckgo_search(query)
        except Exception:
            return None

        if not results:
            return None

        logger.info(
            "web_search",
            extra={
                "query_used": True,
                "sources_count": len(results),
            },
        )

        timestamp = datetime.utcnow().isoformat()

        blocks = [
            f"[Web search results | fetched {timestamp} UTC]"
        ]

        for r in results:
            blocks.append(f"- {r}")

        return "\n".join(blocks)

    # -------------------- Internal --------------------

    def _duckduckgo_search(self, query: str, max_results: int = 5) -> list[str]:
        url = "https://duckduckgo.com/html/"
        params = {"q": query}

        response = requests.get(
            url,
            params=params,
            headers=self.headers,
            timeout=self.timeout
        )

        response.raise_for_status()

        soup = BeautifulSoup(response.text, "html.parser")

        snippets = []
        for result in soup.select(".result__snippet"):
            text = result.get_text(strip=True)
            if text and text not in snippets:
                snippets.append(text)

            if len(snippets) >= max_results:
                break

        return snippets

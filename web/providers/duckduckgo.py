from web.base import BaseWebProvider
from utils.logger import setup_logger
import requests
from bs4 import BeautifulSoup

logger = setup_logger("web.provider.ddg")

class DuckDuckGoProvider(BaseWebProvider):
    def __init__(self, timeout: int = 10):
        self.timeout = timeout
        self.headers = {
            "User-Agent": "Mozilla/5.0 (verysleepy-ai)"
        }

    def search(self, query: str, max_results: int = 5) -> list[str]:
        logger.info("web_search", extra={"provider": "ddg", "query_length": len(query)})
        
        try:
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
        except Exception as e:
            logger.error("web_search_failed", extra={"reason": str(e)})
            return []

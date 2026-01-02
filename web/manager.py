from utils.config import load_config
from utils.logger import setup_logger
from web.crosscheck import crosscheck
from web.formatter import format_for_prompt
from web.providers.duckduckgo import DuckDuckGoProvider

logger = setup_logger("web.manager")
config = load_config()

class WebManager:
    def __init__(self):
        self.provider = DuckDuckGoProvider()

    def run(self, query: str) -> str:
        if not config.get("web", {}).get("enabled", True):
            return ""

        max_sources = config.get("web", {}).get("max_sources", 5)

        results = self.provider.search(query, max_sources)
        results = crosscheck(results)

        logger.info(
            "web_results_ready",
            extra={"sources_count": len(results)},
        )

        return format_for_prompt(results)

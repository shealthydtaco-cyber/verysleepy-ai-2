from abc import ABC, abstractmethod

class BaseWebProvider(ABC):
    @abstractmethod
    def search(self, query: str, max_results: int) -> list[str]:
        """
        Return a list of short text snippets (NOT answers).
        """
        pass

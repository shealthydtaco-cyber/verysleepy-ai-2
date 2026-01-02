from abc import ABC, abstractmethod

class BaseMemory(ABC):
    @abstractmethod
    def read(self) -> str:
        pass

    @abstractmethod
    def write(self, content: str):
        pass

    @abstractmethod
    def clear(self):
        pass

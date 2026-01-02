from abc import ABC, abstractmethod

class BaseTTS(ABC):
    @abstractmethod
    def speak(self, text: str):
        pass

class BaseSTT(ABC):
    @abstractmethod
    def listen(self) -> str:
        pass

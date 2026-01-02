from memory.base import BaseMemory
from utils.logger import setup_logger

logger = setup_logger("memory.nsfw")

class NSFWMemory(BaseMemory):
    def __init__(self, store):
        self.store = store

    def read(self) -> str:
        logger.info("memory_read", extra={"memory_type": "nsfw"})
        return self.store.read()

    def write(self, content: str):
        logger.info("memory_write", extra={"memory_type": "nsfw"})
        self.store.write(content)

    def clear(self):
        self.store.clear()

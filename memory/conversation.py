from memory.base import BaseMemory
from utils.logger import setup_logger

logger = setup_logger("memory.conversation")

class ConversationMemory(BaseMemory):
    def __init__(self, store):
        self.store = store

    def read(self) -> str:
        logger.info("memory_read", extra={"memory_type": "conversation"})
        return self.store.read()

    def write(self, content: str):
        logger.info("memory_write", extra={"memory_type": "conversation"})
        self.store.write(content)

    def clear(self):
        self.store.clear()

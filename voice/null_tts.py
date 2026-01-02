from voice.base import BaseTTS
from utils.logger import setup_logger

logger = setup_logger("voice.null")

class NullTTS(BaseTTS):
    def speak(self, text: str):
        logger.warning("tts_skipped", extra={"reason": "voice_disabled"})

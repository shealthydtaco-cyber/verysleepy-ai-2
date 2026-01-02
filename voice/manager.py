from utils.config import load_config
from utils.logger import setup_logger
from voice.tts import TextToSpeech
from voice.null_tts import NullTTS

logger = setup_logger("voice.manager")
config = load_config()

class VoiceManager:
    def __init__(self, tts: TextToSpeech | None):
        self.enabled = config.get("voice", {}).get("enabled", True)

        if not self.enabled or tts is None:
            self.tts = NullTTS()
        else:
            self.tts = tts

    def speak(self, text: str):
        try:
            self.tts.speak(text)
        except Exception as e:
            logger.error("tts_failed", extra={"error": str(e)})

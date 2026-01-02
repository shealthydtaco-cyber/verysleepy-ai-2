# voice/stt.py

import sounddevice as sd
import logging
import numpy as np
from scipy.io.wavfile import write
from faster_whisper import WhisperModel
import tempfile
import os
from voice.base import BaseSTT
from utils.config import load_config

logger = logging.getLogger("voice")
config = load_config()


class SpeechToText(BaseSTT):
    def __init__(self, model_size: str = None):
        if model_size is None:
            model_size = config.get("voice", {}).get("stt_model", "small")
        self.model = WhisperModel(model_size, compute_type="int8", device="cpu")

    def listen(self, duration: int = 5, sample_rate: int = 16000) -> str:
        logger.info(
            "stt_start",
            extra={
                "duration": duration,
                "model": "faster_whisper",
            },
        )
        
        print("Listening...")

        recording = sd.rec(
            int(duration * sample_rate),
            samplerate=sample_rate,
            channels=1,
            dtype=np.int16
        )
        sd.wait()

        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as f:
            write(f.name, sample_rate, recording)
            temp_path = f.name

        segments, _ = self.model.transcribe(temp_path)
        os.unlink(temp_path)

        text = " ".join(segment.text for segment in segments)
        
        logger.info(
            "stt_complete",
            extra={"text_length": len(text)},
        )
        
        return text.strip()

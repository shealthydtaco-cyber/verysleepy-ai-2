# voice/tts.py

import tempfile
import os
import logging
from pathlib import Path
import winsound
from piper.voice import PiperVoice
import wave
from voice.base import BaseTTS

logger = logging.getLogger("voice")


class TextToSpeech(BaseTTS):
    def __init__(self, piper_binary: Path, voice_model: Path):
        self.voice_path = voice_model

        if not self.voice_path.exists():
            raise FileNotFoundError(f"Voice model not found: {self.voice_path}")
        
        # Load the voice model
        self.voice = PiperVoice.load(str(self.voice_path))

    def speak(self, text: str):
        voice_name = self.voice_path.stem
        
        logger.info(
            "tts_start",
            extra={
                "engine": "piper",
                "voice": voice_name,
            },
        )
        
        try:
            # Get audio chunks from synthesis
            audio_chunks = list(self.voice.synthesize(text))
            
            if not audio_chunks:
                raise ValueError("No audio was generated")
            
            # Save to temporary WAV file
            with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as f:
                wav_path = f.name
            
            # Use the first chunk's parameters (they should all be the same)
            first_chunk = audio_chunks[0]
            
            with wave.open(wav_path, "wb") as wav_file:
                wav_file.setnchannels(first_chunk.sample_channels)
                wav_file.setsampwidth(first_chunk.sample_width)
                wav_file.setframerate(first_chunk.sample_rate)
                
                # Write all audio chunks
                for chunk in audio_chunks:
                    wav_file.writeframes(chunk.audio_int16_bytes)
            
            print(f"Audio file: {wav_path}, Chunks: {len(audio_chunks)}")

            # Play WAV using Windows audio system
            winsound.PlaySound(wav_path, winsound.SND_FILENAME | winsound.SND_NODEFAULT)

            os.unlink(wav_path)
        except Exception as e:
            logger.error(
                "tts_failed",
                extra={"reason": str(e)},
            )
            raise

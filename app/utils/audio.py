"""
app/utils/audio.py
Audio utilities: convert various formats to WAV, validate audio files.
"""

import io
import wave
from typing import Optional


def convert_to_wav(audio_bytes: bytes, source_format: str = "webm") -> bytes:
    """
    Best-effort WAV conversion using pydub/ffmpeg if available,
    otherwise pass through (Whisper accepts many formats natively).
    """
    try:
        from pydub import AudioSegment

        audio = AudioSegment.from_file(io.BytesIO(audio_bytes), format=source_format)
        buf = io.BytesIO()
        audio.export(buf, format="wav")
        return buf.getvalue()
    except Exception:
        # Return as-is; Whisper handles mp3/webm/ogg/mp4 natively
        return audio_bytes


def get_audio_duration(wav_bytes: bytes) -> Optional[float]:
    """Return duration in seconds for a WAV file."""
    try:
        with wave.open(io.BytesIO(wav_bytes)) as wf:
            frames = wf.getnframes()
            rate = wf.getframerate()
            return frames / float(rate)
    except Exception:
        return None


def is_silent(audio_bytes: bytes, threshold: float = 0.01) -> bool:
    """Rough silence detection — checks if max amplitude is below threshold."""
    try:
        from pydub import AudioSegment

        audio = AudioSegment.from_file(io.BytesIO(audio_bytes))
        peak = audio.max_dBFS
        return peak < -40  # dBFS threshold for silence
    except Exception:
        return False

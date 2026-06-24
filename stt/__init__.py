"""Speech-to-text module: records mic audio and transcribes it with Whisper."""

from .record_audio import record_audio
from .whisper_transcribe import transcribe

__all__ = ["record_audio", "transcribe"]
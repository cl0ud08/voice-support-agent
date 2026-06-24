"""
tts/speak.py

Converts text to speech using Microsoft Edge's free TTS service (via edge-tts).
No API key, no quota, no cost — genuinely free.

Provides both sync and async versions:
- speak_to_file_async(): use inside async contexts (e.g. FastAPI WebSocket handlers)
- speak_to_file():       use from plain scripts (calls asyncio.run() internally)
- speak():               converts text and plays it immediately (scripts only)

Run directly to test: python speak.py
"""

import asyncio
import os
import tempfile

import edge_tts
import sounddevice as sd
import soundfile as sf

VOICE = "en-US-GuyNeural"


async def speak_to_file_async(text: str, filename: str = "output.mp3") -> str:
    """
    Converts `text` to speech and saves it as an mp3 file.

    Use this version when you're already inside an async function/event loop
    (e.g. a FastAPI WebSocket handler) — just `await` it directly.

    Args:
        text:     The text to convert to speech.
        filename: Output file path. Defaults to "output.mp3".

    Returns:
        The path of the saved audio file.

    Raises:
        ValueError: If `text` is empty or whitespace-only.
        edge_tts.exceptions.NoAudioReceived: If the TTS service returns no audio.
    """
    if not text or not text.strip():
        raise ValueError("text must be a non-empty string")

    print(f'Generating speech for: "{text}"')
    communicate = edge_tts.Communicate(text, VOICE)
    await communicate.save(filename)
    print(f"Saved to {filename}")
    return filename


def speak_to_file(text: str, filename: str = "output.mp3") -> str:
    """
    Converts `text` to speech and saves it as an mp3 file.

    Use this version from plain, non-async scripts — it starts its own
    event loop via asyncio.run(). Do NOT call this from inside FastAPI
    routes or any already-running event loop; use speak_to_file_async() there.

    Args:
        text:     The text to convert to speech.
        filename: Output file path. Defaults to "output.mp3".

    Returns:
        The path of the saved audio file.
    """
    return asyncio.run(speak_to_file_async(text, filename))


def speak(text: str) -> None:
    """
    Converts `text` to speech and plays it immediately through speakers.

    Uses a temporary file that is automatically cleaned up after playback.
    Sync only — do not call from an async context.

    Args:
        text: The text to convert to speech and play.
    """
    # Use a proper temp file so cleanup is guaranteed even if playback errors
    with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as tmp:
        tmp_path = tmp.name

    try:
        speak_to_file(text, tmp_path)
        data, samplerate = sf.read(tmp_path)
        print("Playing audio...")
        sd.play(data, samplerate)
        sd.wait()
    finally:
        # Always remove the temp file, even if playback raises an exception
        if os.path.exists(tmp_path):
            os.remove(tmp_path)


if __name__ == "__main__":
    speak("Hello! Your order number 1234 has been shipped and will arrive in three days.")
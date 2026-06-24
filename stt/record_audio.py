"""
stt/record_audio.py

Records a few seconds of audio from your microphone and saves it as a .wav file.
Uses `sounddevice` instead of `pyaudio` — better wheel support on Windows,
especially on newer Python versions where pyaudio's build tooling lags behind.

Run directly to test: python record_audio.py
"""

import sounddevice as sd
from scipy.io.wavfile import write as write_wav

# Whisper expects 16kHz mono audio for best results
SAMPLE_RATE = 16000
CHANNELS = 1
RECORD_SECONDS = 5
OUTPUT_FILE = "test_recording.wav"


def record_audio(filename: str = OUTPUT_FILE, duration: int = RECORD_SECONDS) -> str:
    """Records `duration` seconds of mic audio and saves it to `filename`."""
    print(f"Recording for {duration} seconds... speak now.")

    audio_data = sd.rec(
        int(duration * SAMPLE_RATE),
        samplerate=SAMPLE_RATE,
        channels=CHANNELS,
        dtype="int16",
    )
    sd.wait()  # blocks until recording is finished

    print("Done recording.")
    write_wav(filename, SAMPLE_RATE, audio_data)
    print(f"Saved to {filename}")
    return filename


if __name__ == "__main__":
    record_audio()
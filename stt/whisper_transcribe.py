"""
stt/whisper_transcribe.py

Transcribes a .wav file to text using OpenAI's Whisper model, running fully
locally (no API key, no internet required after the model downloads once).

Run directly to test: python whisper_transcribe.py
"""

import whisper

# "base" is the sweet spot for a laptop: ~140MB, decent accuracy, fast enough.
# tiny < base < small < medium < large (slower -> faster, worse -> better accuracy)
MODEL_SIZE = "base"

_model = None  # cached so we don't reload the model on every call


def get_model():
    """Loads the Whisper model once and reuses it (loading takes a few seconds)."""
    global _model
    if _model is None:
        print(f"Loading Whisper '{MODEL_SIZE}' model (first run downloads it)...")
        _model = whisper.load_model(MODEL_SIZE)
    return _model


def transcribe(filepath: str) -> str:
    """Transcribes the audio file at `filepath` and returns the text."""
    model = get_model()
    result = model.transcribe(filepath, fp16=False)  # fp16=False avoids CPU warning
    return result["text"].strip()


if __name__ == "__main__":
    text = transcribe("test_recording.wav")
    print("\nTranscript:")
    print(text)
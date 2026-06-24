"""
stt/test_pipeline.py

The Day 2 deliverable: record 5 seconds from your mic, transcribe it,
print the result. This is what "python test_pipeline.py" runs.
"""

from record_audio import record_audio
from whisper_transcribe import transcribe

if __name__ == "__main__":
    wav_path = record_audio()
    print("\nTranscribing...")
    text = transcribe(wav_path)
    print("\n--- TRANSCRIPT ---")
    print(text)
    print("-------------------")
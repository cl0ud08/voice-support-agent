"""
test_audio_websocket.py

Records 5 seconds from your mic, sends the raw audio bytes over the
/ws/audio WebSocket, prints the transcript + agent response,
and plays back the server's spoken audio reply.
"""

import asyncio
import websockets
import json
import io
import sounddevice as sd
import soundfile as sf

SAMPLE_RATE = 16000
CHANNELS = 1
RECORD_SECONDS = 5


def record_to_bytes() -> bytes:
    """Records mic audio and returns it as in-memory WAV bytes."""
    print(f"Recording for {RECORD_SECONDS} seconds... speak now.")
    audio_data = sd.rec(
        int(RECORD_SECONDS * SAMPLE_RATE),
        samplerate=SAMPLE_RATE,
        channels=CHANNELS,
        dtype="int16",
    )
    sd.wait()
    print("Done recording.")

    buffer = io.BytesIO()
    sf.write(buffer, audio_data, SAMPLE_RATE, format="WAV")
    return buffer.getvalue()


def play_audio_bytes(audio_bytes: bytes) -> None:
    """Plays mp3 bytes through speakers using sounddevice + soundfile."""
    data, samplerate = sf.read(io.BytesIO(audio_bytes))
    print("Playing agent's spoken reply...")
    sd.play(data, samplerate)
    sd.wait()


async def test_audio():
    uri = "ws://127.0.0.1:8000/ws/audio"

    async with websockets.connect(uri) as websocket:
        audio_bytes = record_to_bytes()

        print("Sending audio to server...")
        await websocket.send(audio_bytes)

        print("Waiting for transcription + response...")
        text_response = await websocket.recv()
        data = json.loads(text_response)

        print("\n--- RESULT ---")
        print(f"Transcript: {data['transcript']}")
        print(f"Intent: {data['intent']}")
        print(f"Response: {data['response']}")

        print("\nWaiting for spoken audio reply...")
        audio_reply = await websocket.recv()
        print(f"Received {len(audio_reply)} bytes of audio reply.")

        play_audio_bytes(audio_reply)


if __name__ == "__main__":
    asyncio.run(test_audio())
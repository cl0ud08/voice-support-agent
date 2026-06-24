"""
main.py

FastAPI backend exposing the voice support agent over HTTP and WebSocket.
Run with: uvicorn main:app --reload
"""

import tempfile
import os
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from pydantic import BaseModel
from agent.graph import build_graph
from stt.whisper_transcribe import transcribe
from tts.speak import speak_to_file_async
import subprocess

app = FastAPI(title="Voice Support Agent API")
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)
# Build the graph once at startup, reuse it for every request.
graph = build_graph()


class ChatRequest(BaseModel):
    text: str


class ChatResponse(BaseModel):
    response: str
    intent: str


@app.get("/")
def health_check():
    """Simple endpoint to confirm the server is alive."""
    return {"status": "ok", "service": "voice-support-agent"}


@app.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest):
    """
    Takes user text, runs it through the LangGraph agent,
    returns the classified intent and the agent's response.
    """
    result = graph.invoke({
        "user_input": request.text,
        "intent": None,
        "response": None,
    })

    return ChatResponse(
        response=result["response"],
        intent=result["intent"],
    )


@app.websocket("/ws/chat")
async def websocket_chat(websocket: WebSocket):
    """
    Persistent WebSocket connection. Client sends text messages,
    server runs them through the agent and sends back responses.
    Stays open until the client disconnects.
    """
    await websocket.accept()
    print("Client connected.")

    try:
        while True:
            user_text = await websocket.receive_text()
            print(f"Received: {user_text}")

            result = graph.invoke({
                "user_input": user_text,
                "intent": None,
                "response": None,
            })

            await websocket.send_json({
                "response": result["response"],
                "intent": result["intent"],
            })

    except WebSocketDisconnect:
        print("Client disconnected.")


@app.websocket("/ws/audio")
async def websocket_audio(websocket: WebSocket):
    """
    Receives raw audio bytes from the client, transcribes with Whisper,
    runs the transcript through the agent, converts the reply to speech,
    and sends back both the text metadata AND the spoken audio.
    """
    await websocket.accept()
    print("Audio client connected.")

    try:
        while True:
            audio_bytes = await websocket.receive_bytes()
            print(f"Received {len(audio_bytes)} bytes of audio.")

            # Browser sends webm/opus audio — save it as-is first
            with tempfile.NamedTemporaryFile(suffix=".webm", delete=False) as tmp:
                tmp.write(audio_bytes)
                webm_path = tmp.name

            # Convert to wav using ffmpeg, since Whisper expects wav
            wav_path = webm_path.replace(".webm", ".wav")
            subprocess.run(
                ["ffmpeg", "-y", "-i", webm_path, "-ar", "16000", "-ac", "1", wav_path],
                capture_output=True,
                check=True,
            )

            tmp_path = wav_path  # so the existing cleanup code below still works

            tts_path = None
            try:
                transcript = transcribe(tmp_path)
                print(f"Transcript: {transcript}")

                result = graph.invoke({
                    "user_input": transcript,
                    "intent": None,
                    "response": None,
                })

                # Send the text metadata first, so the client knows what's coming
                await websocket.send_json({
                    "transcript": transcript,
                    "response": result["response"],
                    "intent": result["intent"],
                })

                # Convert the response text to speech, then stream the audio bytes
                tts_path = await speak_to_file_async(result["response"], filename="_server_reply.mp3")
                with open(tts_path, "rb") as f:
                    audio_reply_bytes = f.read()

                await websocket.send_bytes(audio_reply_bytes)
                print(f"Sent {len(audio_reply_bytes)} bytes of reply audio.")

            finally:
                os.unlink(webm_path)
                if os.path.exists(wav_path):
                    os.unlink(wav_path)
                if tts_path and os.path.exists(tts_path):
                    os.unlink(tts_path)
    except WebSocketDisconnect:
        print("Audio client disconnected.")
# 📦 Voice Shipment Tracker

A real-time voice AI agent for courier & logistics support. Ask it out loud
where your package is, and it transcribes your question, classifies what you
want, looks up real shipment data, and **speaks the answer back** — all over
a live WebSocket connection.

---
## Demo
https://github.com/user-attachments/assets/ded6a27d-6dd3-4df9-8fc4-ff9c9b62fd89

## What it does

Speak a question like:

- *"Where is shipment 1234?"*
- *"My package never arrived."*
- *"I'd like a refund for my order."*

The agent:

1. **Transcribes** your voice (Whisper, running locally)
2. **Classifies intent** — shipment status, delivery issue, refund, or general (Groq LLM)
3. **Looks up real data** — status, current location, estimated delivery (SQLite, via an MCP tool)
4. **Replies out loud** — converts its text response to speech (Edge-TTS) and streams it back

All of this happens over a single persistent WebSocket connection, so the
interaction feels like a real conversation, not a form submission.

---

## Architecture

```
   🎤 Mic (browser)
     │  webm audio
     ▼
 ┌──────────────┐
 │   FastAPI    │  WebSocket /ws/audio
 │   backend    │
 └──────┬───────┘
        │ ffmpeg: webm → wav
        ▼
 ┌─────────────┐      ┌─────────────┐      ┌───────────────┐      ┌─────────────┐
 │   Whisper   │ ───▶ │  LangGraph  │ ───▶ │   MCP Tool    │ ───▶ │  Edge-TTS   │
 │    (STT)    │      │   (brain)   │      │ (shipment DB) │      │    (TTS)    │
 └─────────────┘      └─────────────┘      └───────────────┘      └──────┬──────┘
                                                                          │
                                                                          ▼
                                                                   🔊 Speaker (browser)
```

- **STT (Speech-to-Text):** OpenAI Whisper, running fully locally — free, no API limits, no internet dependency after the model downloads once.
- **Agent brain:** a LangGraph state graph with two nodes — `classify_node` (intent classification via Groq) and `respond_node` (looks up data and builds the reply).
- **Intent classification:** Groq (`llama-3.1-8b-instant`), called with `temperature=0` and structured JSON output for deterministic, parseable results. Falls back gracefully to a default intent if the LLM call fails for any reason.
- **Tool calling:** an MCP (Model Context Protocol) server exposing a `get_shipment_status` tool, backed by a mock SQLite database of shipments.
- **TTS (Text-to-Speech):** Microsoft Edge's free neural voices via `edge-tts` — unlimited, no API key, no cost.
- **Backend:** FastAPI, with both REST (`/chat`) and WebSocket (`/ws/chat`, `/ws/audio`) endpoints.
- **Frontend:** React + TypeScript (Vite), with a live "shipment journey" visualization that animates through each pipeline stage in real time as a request is processed.
- **Containerization:** Dockerized backend on a pinned Python 3.11 base image for reproducible builds.

---

## Tech stack

| Layer              | Tool                                  | Why                                              |
|---------------------|----------------------------------------|---------------------------------------------------|
| STT                 | OpenAI Whisper (local)                | Free, no quota, runs offline after model download |
| Agent orchestration | LangGraph                             | State machine for classify → respond flow         |
| LLM                 | Groq (`llama-3.1-8b-instant`)         | Free tier, very low latency                        |
| Tool calling        | MCP (Model Context Protocol)          | Standardized agent-callable tool interface         |
| TTS                 | Edge-TTS                              | Free, unlimited, no API key                        |
| Backend             | FastAPI + WebSockets                  | Async, real-time, auto-generated docs              |
| Frontend            | React + TypeScript + Vite             | Type-safe, fast dev loop                           |
| Database            | SQLite                                | Zero-setup, file-based, perfect for a demo dataset |
| Audio conversion    | ffmpeg                                | Browser records webm; Whisper needs wav            |
| Containerization    | Docker                                | Reproducible runtime, isolated from host Python    |

**Why no paid services:** every component above runs on a genuinely free
tier or is fully open-source/local. ElevenLabs was the original plan for
TTS, but its free tier no longer permits API access to any voice (library
or cloned) without a paid plan — so the project pivoted to Edge-TTS, which
has no such restriction.

---

## Project structure

```
voice-support-agent/
├── agent/              # LangGraph state graph: state, nodes, graph definition
├── data/               # SQLite seed script + shipment lookup logic
├── mcp_server/         # MCP tool server wrapping the shipment lookup
├── stt/                # Mic recording + Whisper transcription
├── tts/                # Edge-TTS speech generation (sync + async versions)
├── frontend/           # React + TypeScript UI
│   └── src/
│       ├── App.tsx      # Mic button, WebSocket client, journey visualization
│       └── App.css
├── main.py             # FastAPI app: REST + WebSocket endpoints
├── requirements.txt
├── Dockerfile
├── .dockerignore
├── .env.example
└── README.md
```

---

## Running it locally

### Backend

```bash
git clone https://github.com/YOUR_USERNAME/voice-support-agent.git
cd voice-support-agent
python -m venv venv
venv\Scripts\activate        # Windows
pip install -r requirements.txt
cp .env.example .env         # then fill in your GROQ_API_KEY

python data/seed_db.py       # seed the mock shipment database
uvicorn main:app --reload
```

Backend runs at `http://127.0.0.1:8000` — interactive API docs at `/docs`.

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Frontend runs at `http://localhost:5173`.

### Running the backend in Docker instead

```bash
docker build -t voice-support-agent-backend .
docker run -p 8000:8000 --env-file .env voice-support-agent-backend
```

---

## Key engineering decisions

A few choices worth highlighting (and good talking points if asked about
this project):

- **Defensive LLM calls:** `classify_node` wraps its Groq call in a
  try/except — a malformed transcript or API hiccup degrades to a default
  intent instead of crashing the WebSocket connection.
- **Async-safe TTS:** `tts/speak.py` exposes both a sync (`speak_to_file`,
  for standalone scripts) and async (`speak_to_file_async`, for use inside
  FastAPI's already-running event loop) version of the same function, to
  avoid the classic `asyncio.run() cannot be called from a running event
  loop` error.
- **Format conversion at the boundary:** browsers record audio as
  `webm`/`opus`; Whisper expects `wav`. The backend converts with `ffmpeg`
  immediately on receipt, keeping every downstream component working with
  one consistent format.
- **Pinned Python version in Docker:** local development uses Python 3.14;
  the Docker image deliberately pins Python 3.11, since several
  dependencies (Whisper/PyTorch, MCP/Starlette) had compatibility issues on
  the newest Python at the time of building this.
- **Graceful degradation everywhere:** empty transcripts, denied microphone
  permissions, dropped WebSocket connections, and failed audio conversions
  all surface a clear, specific message instead of a frozen UI or an
  unhandled exception.

---


## License

MIT

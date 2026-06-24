import { useRef, useState } from "react";
import "./App.css";

type AgentResult = {
  transcript: string;
  response: string;
  intent: string;
};

type AppStatus = "idle" | "recording" | "processing" | "speaking" | "error";
type JourneyStage = "captured" | "transcribed" | "understood" | "located" | "replied";

const STAGES: { key: JourneyStage; label: string }[] = [
  { key: "captured",    label: "Voice captured"    },
  { key: "transcribed", label: "Transcribed"        },
  { key: "understood",  label: "Intent understood"  },
  { key: "located",     label: "Shipment found"     },
  { key: "replied",     label: "Reply spoken"       },
];

const STAGE_FILL: Record<JourneyStage, number> = {
  captured: 0, transcribed: 25, understood: 50, located: 75, replied: 100,
};

const STATUS_LABEL: Record<AppStatus, string> = {
  idle:       "Tap to ask about your shipment",
  recording:  "Listening…",
  processing: "Tracking your shipment…",
  speaking:   "Speaking reply…",
  error:      "Something went wrong — tap to retry",
};

// ─── Icons ────────────────────────────────────────────────────────────────────

function TruckIcon() {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8">
      <rect x="1" y="6" width="14" height="10" rx="1.5" />
      <path d="M15 9h4l3 3v4h-7z" />
      <circle cx="6"    cy="18" r="1.5" />
      <circle cx="17.5" cy="18" r="1.5" />
    </svg>
  );
}

function MicIcon() {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8">
      <path d="M12 1a3 3 0 0 0-3 3v8a3 3 0 0 0 6 0V4a3 3 0 0 0-3-3z" />
      <path d="M19 10v2a7 7 0 0 1-14 0v-2" strokeLinecap="round" />
      <line x1="12" y1="19" x2="12" y2="23" strokeLinecap="round" />
      <line x1="8"  y1="23" x2="16" y2="23" strokeLinecap="round" />
    </svg>
  );
}

function StopIcon() {
  return (
    <svg viewBox="0 0 24 24" fill="currentColor">
      <rect x="6" y="6" width="12" height="12" rx="2.5" />
    </svg>
  );
}

function CheckIcon() {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
      <polyline points="20 6 9 17 4 12" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  );
}

function PackageIcon() {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8">
      <path d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z" />
      <polyline points="3.27 6.96 12 12.01 20.73 6.96" />
      <line x1="12" y1="22.08" x2="12" y2="12" />
    </svg>
  );
}

const STAGE_ICONS: Record<JourneyStage, JSX.Element> = {
  captured: (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
      <path d="M12 1a3 3 0 0 0-3 3v8a3 3 0 0 0 6 0V4a3 3 0 0 0-3-3z" />
      <path d="M19 10v2a7 7 0 0 1-14 0v-2" strokeLinecap="round" />
    </svg>
  ),
  transcribed: (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
      <path d="M4 6h16M4 12h16M4 18h10" strokeLinecap="round" />
    </svg>
  ),
  understood: (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
      <circle cx="12" cy="12" r="9" />
      <path d="M9.5 9.5a2.5 2.5 0 1 1 3.5 2.3c-.6.3-1 .9-1 1.7v.5" strokeLinecap="round" />
      <circle cx="12" cy="17" r="0.5" fill="currentColor" />
    </svg>
  ),
  located: (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
      <path d="M12 22s7-7.4 7-12a7 7 0 1 0-14 0c0 4.6 7 12 7 12z" />
      <circle cx="12" cy="10" r="2.5" />
    </svg>
  ),
  replied: (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
      <path d="M11 5 6 9H2v6h4l5 4z" strokeLinecap="round" strokeLinejoin="round" />
      <path d="M15.5 8.5a5 5 0 0 1 0 7" strokeLinecap="round" />
    </svg>
  ),
};

// ─── App ──────────────────────────────────────────────────────────────────────

function App() {
  const [status,      setStatus]      = useState<AppStatus>("idle");
  const [result,      setResult]      = useState<AgentResult | null>(null);
  const [activeStage, setActiveStage] = useState<JourneyStage | null>(null);
  const [doneStages,  setDoneStages]  = useState<Set<JourneyStage>>(new Set());
  const [latencyMs,   setLatencyMs]   = useState<number | null>(null);

  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const chunksRef        = useRef<Blob[]>([]);
  const startTimeRef     = useRef<number>(0);

  const isRecording = status === "recording";
  const isBusy      = status === "recording" || status === "processing" || status === "speaking";

  const lastDone    = Array.from(doneStages).slice(-1)[0] as JourneyStage | undefined;
  const fillPercent = lastDone ? STAGE_FILL[lastDone] : 0;

  const resetJourney  = () => { setDoneStages(new Set()); setActiveStage(null); };
  const advanceStage  = (s: JourneyStage) => setActiveStage(s);
  const completeStage = (s: JourneyStage) =>
    setDoneStages((prev) => new Set(prev).add(s));

  const startRecording = async () => {
    setResult(null);
    setLatencyMs(null);
    resetJourney();
    try {
      const stream   = await navigator.mediaDevices.getUserMedia({ audio: true });
      const recorder = new MediaRecorder(stream);
      mediaRecorderRef.current = recorder;
      chunksRef.current        = [];

      recorder.ondataavailable = (e) => { if (e.data.size > 0) chunksRef.current.push(e.data); };
      recorder.onstop = () => {
        stream.getTracks().forEach((t) => t.stop());
        completeStage("captured");
        sendAudioToServer(new Blob(chunksRef.current, { type: "audio/webm" }));
      };

      recorder.start();
      advanceStage("captured");
      setStatus("recording");
    } catch {
      setStatus("error");
    }
  };

  const stopRecording = () => {
    mediaRecorderRef.current?.stop();
    setStatus("processing");
    advanceStage("transcribed");
    startTimeRef.current = performance.now();
  };

  // ─── WebSocket send & receive ──────────────────────────────────────────────
  // NOTE: The backend sends exactly TWO frames per request, then stays open:
  //   Frame 1 → text  (JSON metadata: transcript, intent, response)
  //   Frame 2 → bytes (the full .mp3 audio, sent as a single blob)
  // We do NOT wait for ws.onclose — it never fires because the backend
  // keeps the connection alive for the next query.

  const sendAudioToServer = (audioBlob: Blob) => {
    const ws = new WebSocket("ws://127.0.0.1:8000/ws/audio");

    ws.onopen = async () => {
      ws.send(await audioBlob.arrayBuffer());
    };

    let gotMetadata = false;

    ws.onmessage = async (event) => {

      // ── Frame 1: JSON metadata ─────────────────────────────────────────
      if (!gotMetadata) {
        gotMetadata = true;

        const data = JSON.parse(event.data as string) as AgentResult;
        setResult(data);
        setLatencyMs(Math.round(performance.now() - startTimeRef.current));

        completeStage("transcribed");
        completeStage("understood");
        completeStage("located");
        advanceStage("replied");
        setStatus("speaking");
        return;
      }

      // ── Frame 2: raw audio bytes (.mp3) ───────────────────────────────
      // The backend sends the entire audio as one binary frame.
      // event.data is a Blob here — create an object URL and play directly.
      if (event.data instanceof Blob) {
        const url = URL.createObjectURL(event.data);  // already audio/mpeg
        const audio = new Audio(url);

        audio.onended = () => {
          URL.revokeObjectURL(url);
          completeStage("replied");
          setActiveStage(null);
          setStatus("idle");
          // Close the WebSocket after the reply is fully played.
          // This keeps one connection per voice turn (clean, simple).
          ws.close();
        };

        audio.onerror = (e) => {
          console.error("Audio playback error:", e);
          URL.revokeObjectURL(url);
          setStatus("error");
          ws.close();
        };

        audio.play().catch((err) => {
          // Autoplay was blocked — shouldn't happen since the user just
          // interacted with the mic button, but log it clearly if it does.
          console.error("Autoplay blocked:", err);
          URL.revokeObjectURL(url);
          setStatus("error");
          ws.close();
        });
      }
    };

    ws.onerror = (err) => {
      console.error("WebSocket error:", err);
      setStatus("error");
    };
  };
  const handleButton = () => {
    if (isRecording) stopRecording();
    else if (status === "idle" || status === "error") startRecording();
  };

  const intentLabel = (raw: string) =>
    raw.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase());

  return (
    <div className="app">
      <div className="card">

        {/* Brand */}
        <div className="brand">
          <div className="brand-icon"><TruckIcon /></div>
          <div>
            <div className="brand-text">Delivery Voice Agent</div>
            <div className="brand-sub">Ask about any shipment</div>
          </div>
        </div>

        {/* Progress steps */}
        <div className="steps">
          <div className="connector-bg" />
          <div className="connector-fill" style={{ width: `${fillPercent}%` }} />
          {STAGES.map((stage) => {
            const isDone   = doneStages.has(stage.key);
            const isActive = activeStage === stage.key && !isDone;
            return (
              <div key={stage.key} className="step">
                <div className={`step-dot ${isDone ? "done" : ""} ${isActive ? "active" : ""}`}>
                  {isDone ? <CheckIcon /> : STAGE_ICONS[stage.key]}
                </div>
                <span className={`step-label ${isDone ? "done" : ""} ${isActive ? "active" : ""}`}>
                  {stage.label}
                </span>
              </div>
            );
          })}
        </div>

        {/* Mic zone */}
        <div className="mic-zone">
          <div className={`wave ${isRecording ? "recording" : ""}`}>
            {[1, 2, 3, 4, 5].map((i) => <div key={i} className="wave-bar" />)}
          </div>

          <div className={`mic-ring ${isRecording ? "recording" : ""}`}>
            <button
              className={`mic-btn ${isRecording ? "recording" : ""}`}
              onClick={handleButton}
              disabled={isBusy && !isRecording}
              aria-label={isRecording ? "Stop recording" : "Start recording"}
            >
              {isRecording ? <StopIcon /> : <MicIcon />}
            </button>
          </div>

          <span className={`status-text ${status !== "idle" ? "active" : ""}`}>
            {STATUS_LABEL[status]}
          </span>

          {latencyMs !== null && (
            <span className="latency-text">Response in {(latencyMs / 1000).toFixed(2)}s</span>
          )}
        </div>

        {/* Result panel */}
        {result ? (
          <div className="result">
            <div className="result-row">
              <span className="result-label">You said</span>
              <span className="result-value muted">{result.transcript}</span>
            </div>
            <div className="result-row">
              <span className="result-label">Intent</span>
              <span className="intent-badge"><PackageIcon />{intentLabel(result.intent)}</span>
            </div>
            <div className="result-row">
              <span className="result-label">Reply</span>
              <span className="result-value">{result.response}</span>
            </div>
          </div>
        ) : status !== "error" ? (
          <p className="hint">
            Try saying <strong>"Where is my order #4821?"</strong>{" "}
            or <strong>"Is my package delayed?"</strong>
          </p>
        ) : null}

        {/* Error */}
        {status === "error" && (
          <div className="error-banner">
            Could not connect or access your microphone. Make sure your backend is running
            at <code>ws://127.0.0.1:8000/ws/audio</code> and tap to retry.
          </div>
        )}

      </div>
    </div>
  );
}

export default App;
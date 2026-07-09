#!/usr/bin/env python3
"""HTTP API that keeps MisoTTS loaded in GPU memory for the web demo."""

from __future__ import annotations

import base64
import importlib.util
import io
import os
import threading
import uuid
from contextlib import asynccontextmanager
from dataclasses import dataclass, field
from typing import Dict, List, Optional

os.environ.setdefault("HF_HUB_ETAG_TIMEOUT", "60")
os.environ.setdefault("HF_HUB_DOWNLOAD_TIMEOUT", "60")
os.environ.setdefault("NO_TORCH_COMPILE", "1")

import numpy as np
import soundfile as sf
import torch
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field


def _load_patch() -> None:
    spec = importlib.util.spec_from_file_location(
        "patch_torchaudio",
        "/app/scripts/patch_torchaudio.py",
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)


_load_patch()

from generator import Segment, load_miso_8b  # noqa: E402


@dataclass
class SessionState:
    segments: List[Segment] = field(default_factory=list)
    lock: threading.Lock = field(default_factory=threading.Lock)


class SpeakRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=2000)
    session_id: Optional[str] = None
    speaker: int = 0
    max_audio_length_ms: int = 15_000


class SpeakResponse(BaseModel):
    session_id: str
    sample_rate: int
    audio_base64: str
    text: str


class HealthResponse(BaseModel):
    status: str
    device: str
    model: str
    active_sessions: int


generator = None
sample_rate = 24_000
sessions: Dict[str, SessionState] = {}
sessions_lock = threading.Lock()


def _wav_bytes(audio: torch.Tensor, rate: int) -> bytes:
    buffer = io.BytesIO()
    samples = audio.detach().cpu().numpy().astype(np.float32)
    sf.write(buffer, samples, rate, format="WAV", subtype="PCM_16")
    return buffer.getvalue()


@asynccontextmanager
async def lifespan(_app: FastAPI):
    global generator, sample_rate
    device = "cuda" if torch.cuda.is_available() else "cpu"
    model_source = os.environ.get("MISO_TTS_8B_MODEL", "MisoLabs/MisoTTS")
    print(f"Loading MisoTTS on {device} from {model_source}")
    generator = load_miso_8b(device=device, model_path_or_repo_id=model_source)
    sample_rate = generator.sample_rate
    print(f"Miso API ready (sample_rate={sample_rate})")
    yield
    sessions.clear()


app = FastAPI(title="Miso TTS API", lifespan=lifespan)


@app.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    if generator is None:
        raise HTTPException(status_code=503, detail="Model not loaded")
    return HealthResponse(
        status="ok",
        device=str(generator.device),
        model=os.environ.get("MISO_TTS_8B_MODEL", "MisoLabs/MisoTTS"),
        active_sessions=len(sessions),
    )


@app.post("/v1/speak", response_model=SpeakResponse)
def speak(request: SpeakRequest) -> SpeakResponse:
    if generator is None:
        raise HTTPException(status_code=503, detail="Model not loaded")

    session_id = request.session_id or str(uuid.uuid4())
    with sessions_lock:
        state = sessions.setdefault(session_id, SessionState())

    with state.lock:
        audio = generator.generate(
            text=request.text,
            speaker=request.speaker,
            context=list(state.segments),
            max_audio_length_ms=request.max_audio_length_ms,
        )
        state.segments.append(
            Segment(
                text=request.text,
                speaker=request.speaker,
                audio=audio,
            )
        )

    wav = _wav_bytes(audio, sample_rate)
    return SpeakResponse(
        session_id=session_id,
        sample_rate=sample_rate,
        audio_base64=base64.b64encode(wav).decode("ascii"),
        text=request.text,
    )


@app.delete("/v1/session/{session_id}")
def reset_session(session_id: str) -> JSONResponse:
    with sessions_lock:
        sessions.pop(session_id, None)
    return JSONResponse({"status": "ok", "session_id": session_id})


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        app,
        host="0.0.0.0",
        port=int(os.environ.get("MISO_API_PORT", "8080")),
        log_level="info",
    )
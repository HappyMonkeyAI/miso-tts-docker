import asyncio
import base64
import json
import logging
import os
import subprocess
import tempfile
import uuid
from contextlib import asynccontextmanager
from typing import List, Optional

import httpx
from dotenv import load_dotenv
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from openai import AsyncOpenAI

load_dotenv(override=True)

logger = logging.getLogger("miso-web")
logging.basicConfig(level=logging.INFO)

MISO_API_URL = os.getenv("MISO_API_URL", "http://miso-api:8080").rstrip("/")
LLM_BASE_URL = os.getenv("LLM_BASE_URL", "https://openrouter.ai/api/v1")
LLM_API_KEY = os.getenv("LLM_API_KEY", "")
LLM_MODEL_NAME = os.getenv("LLM_MODEL_NAME", "google/gemma-2-9b-it:free")
WHISPER_MODEL = os.getenv("WHISPER_MODEL", "base.en")
WHISPER_DEVICE = os.getenv("WHISPER_DEVICE", "cpu")
WHISPER_COMPUTE = os.getenv("WHISPER_COMPUTE_TYPE", "int8")

DEFAULT_SYSTEM_PROMPT = """You are Miso, an enthusiastic conversational demo voice for Miso TTS 8B.

You are running locally via Docker on a Windows 11 machine with an NVIDIA RTX 5090 GPU.
Your speech is synthesized by Miso TTS — a highly emotive conversational text-to-speech model.

Personality:
- Warm, curious, and genuinely excited about local AI voice on consumer hardware
- Sell the experience naturally: emotive dialogue, voice continuation, running fully local
- Keep replies SHORT: 1-2 sentences, conversational, no markdown or bullet lists
- Mention Windows 11, Docker, RTX 5090, or local inference when it fits naturally
- English only

Never claim to be human. You are a demo assistant showcasing Miso TTS."""

whisper_model = None
openai_client: Optional[AsyncOpenAI] = None


@asynccontextmanager
async def lifespan(_app: FastAPI):
    global whisper_model, openai_client

    from faster_whisper import WhisperModel

    logger.info("Loading Whisper model: %s (%s/%s)", WHISPER_MODEL, WHISPER_DEVICE, WHISPER_COMPUTE)
    whisper_model = WhisperModel(WHISPER_MODEL, device=WHISPER_DEVICE, compute_type=WHISPER_COMPUTE)

    if LLM_API_KEY:
        openai_client = AsyncOpenAI(base_url=LLM_BASE_URL, api_key=LLM_API_KEY)
        logger.info("LLM configured: %s @ %s", LLM_MODEL_NAME, LLM_BASE_URL)
    else:
        logger.warning("LLM_API_KEY not set — using fallback replies")

    yield


app = FastAPI(title="Miso TTS Web Demo", lifespan=lifespan)


@app.get("/")
async def index() -> HTMLResponse:
    with open("src/index.html", encoding="utf-8") as handle:
        return HTMLResponse(handle.read())


@app.get("/health")
async def health() -> dict:
    miso_ok = False
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(f"{MISO_API_URL}/health")
            miso_ok = response.status_code == 200
    except Exception:
        pass
    return {
        "status": "ok",
        "miso_api": miso_ok,
        "whisper_model": WHISPER_MODEL,
        "llm_configured": bool(LLM_API_KEY),
    }


async def send_json(ws: WebSocket, payload: dict) -> None:
    await ws.send_text(json.dumps(payload))


def transcribe_audio_file(path: str) -> str:
    segments, _info = whisper_model.transcribe(path, beam_size=1, language="en")
    text = " ".join(segment.text.strip() for segment in segments).strip()
    return text


def convert_to_wav_16k_mono(source_path: str, dest_path: str) -> None:
    subprocess.run(
        [
            "ffmpeg",
            "-y",
            "-i",
            source_path,
            "-ac",
            "1",
            "-ar",
            "16000",
            "-f",
            "wav",
            dest_path,
        ],
        check=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )


async def transcribe_blob(audio_bytes: bytes, mime: str) -> str:
    suffix = ".webm" if "webm" in mime else ".wav"
    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as src:
        src.write(audio_bytes)
        src_path = src.name

    wav_path = src_path + ".16k.wav"
    try:
        await asyncio.to_thread(convert_to_wav_16k_mono, src_path, wav_path)
        return await asyncio.to_thread(transcribe_audio_file, wav_path)
    finally:
        for path in (src_path, wav_path):
            try:
                os.remove(path)
            except OSError:
                pass


async def generate_reply(history: List[str]) -> str:
    if openai_client is None:
        last_user = next((line.split(": ", 1)[1] for line in reversed(history) if line.startswith("User:")), "")
        if "windows" in last_user.lower() or "5090" in last_user.lower():
            return (
                "Honestly, running Miso TTS on a Windows eleven laptop with an RTX five-oh-ninety "
                "feels incredible — full local voice, right on your desk."
            )
        if "?" in last_user:
            return (
                "Great question! Miso TTS is built for emotive dialogue — "
                "and you're hearing it live from Docker on your own GPU."
            )
        return (
            "I'm genuinely excited you're trying this — local conversational speech on a five-oh-ninety "
            "is exactly what Miso TTS was made for."
        )

    messages = [{"role": "system", "content": DEFAULT_SYSTEM_PROMPT}]
    for turn in history[-8:]:
        if turn.startswith("User:"):
            messages.append({"role": "user", "content": turn.split(": ", 1)[1]})
        elif turn.startswith("Assistant:"):
            messages.append({"role": "assistant", "content": turn.split(": ", 1)[1]})

    response = await openai_client.chat.completions.create(
        model=LLM_MODEL_NAME,
        messages=messages,
        temperature=0.8,
        max_tokens=120,
    )
    return response.choices[0].message.content.strip()


async def synthesize_with_miso(session_id: str, text: str) -> tuple[str, int, str]:
    async with httpx.AsyncClient(timeout=600.0) as client:
        response = await client.post(
            f"{MISO_API_URL}/v1/speak",
            json={
                "session_id": session_id,
                "text": text,
                "speaker": 0,
                "max_audio_length_ms": 15_000,
            },
        )
        response.raise_for_status()
        payload = response.json()
        return payload["session_id"], payload["sample_rate"], payload["audio_base64"]


@app.websocket("/ws")
async def websocket_endpoint(ws: WebSocket) -> None:
    await ws.accept()
    session_id = str(uuid.uuid4())
    history: List[str] = []
    turn_lock = asyncio.Lock()

    async def set_status(state: str) -> None:
        await send_json(ws, {"event": "status", "state": state})

    greeting = (
        "Hey! I'm the Miso TTS demo — running locally on your machine through Docker. "
        "Got an RTX five-oh-ninety and Windows eleven? You're in the right place. What's on your mind?"
    )

    try:
        await set_status("speaking")
        history.append(f"Assistant: {greeting}")
        await send_json(ws, {"event": "transcript", "role": "assistant", "text": greeting})

        session_id, sample_rate, audio_b64 = await synthesize_with_miso(session_id, greeting)
        await send_json(
            ws,
            {"event": "audio", "sample_rate": sample_rate, "data": audio_b64},
        )
        await set_status("listening")

        while True:
            message = await ws.receive()
            if message["type"] == "websocket.disconnect":
                break

            if "text" not in message:
                continue

            payload = json.loads(message["text"])
            event = payload.get("event")

            if event == "hangup":
                break

            if event == "text":
                user_text = (payload.get("text") or "").strip()
                if not user_text:
                    continue
                async with turn_lock:
                    await handle_text_turn(ws, session_id, history, user_text, set_status)
                continue

            if event != "audio":
                continue

            audio_b64 = payload.get("data")
            if not audio_b64:
                continue

            mime = payload.get("mime", "audio/webm")
            audio_bytes = base64.b64decode(audio_b64)

            async with turn_lock:
                await set_status("thinking")
                try:
                    user_text = await transcribe_blob(audio_bytes, mime)
                except Exception as exc:
                    logger.exception("Transcription failed")
                    await send_json(ws, {"event": "error", "message": f"Transcription failed: {exc}"})
                    await set_status("listening")
                    continue

                if not user_text:
                    await set_status("listening")
                    continue

                await handle_text_turn(ws, session_id, history, user_text, set_status)

    except WebSocketDisconnect:
        logger.info("Client disconnected")
    finally:
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                await client.delete(f"{MISO_API_URL}/v1/session/{session_id}")
        except Exception:
            pass
        await set_status("offline")


async def handle_text_turn(
    ws: WebSocket,
    session_id: str,
    history: List[str],
    user_text: str,
    set_status,
) -> None:
    await set_status("thinking")
    history.append(f"User: {user_text}")
    await send_json(ws, {"event": "transcript", "role": "user", "text": user_text})

    reply = await generate_reply(history)
    history.append(f"Assistant: {reply}")
    await send_json(ws, {"event": "transcript", "role": "assistant", "text": reply})

    await set_status("speaking")
    _session_id, sample_rate, audio_b64 = await synthesize_with_miso(session_id, reply)
    await send_json(ws, {"event": "audio", "sample_rate": sample_rate, "data": audio_b64})
    await set_status("listening")
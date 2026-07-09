import asyncio
import base64
import json
import logging
import os
import subprocess
import tempfile
import uuid
from urllib.parse import urlencode
from contextlib import asynccontextmanager
from dataclasses import dataclass
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
POCKET_API_URL = os.getenv("POCKET_API_URL", "http://pocket-api:8090").rstrip("/")
DEFAULT_TTS_BACKEND = os.getenv("TTS_BACKEND", "pocket").strip().lower()
def _normalize_llm_base_url(url: str) -> str:
    normalized = url.rstrip("/")
    # LM Studio OpenAI-compatible server uses /v1, not /api/v1
    if normalized.endswith("/api/v1"):
        normalized = f"{normalized[:-len('/api/v1')]}/v1"
    return normalized


LLM_BASE_URL = _normalize_llm_base_url(
    os.getenv("LLM_BASE_URL", "https://openrouter.ai/api/v1")
)
LLM_API_KEY = os.getenv("LLM_API_KEY", "")
LLM_MODEL_NAME = os.getenv("LLM_MODEL_NAME", "google/gemma-2-9b-it:free")
WHISPER_MODEL = os.getenv("WHISPER_MODEL", "base.en")
WHISPER_DEVICE = os.getenv("WHISPER_DEVICE", "cpu")
WHISPER_COMPUTE = os.getenv("WHISPER_COMPUTE_TYPE", "int8")
POCKET_SAMPLE_RATE = 24_000

DEFAULT_SYSTEM_PROMPT = """You are Miso, an enthusiastic conversational demo voice assistant.

You are running locally via Docker on a Windows 11 machine with an NVIDIA RTX 5090 GPU.
Your speech is synthesized by local text-to-speech (Miso TTS or Pocket TTS depending on mode).

Personality:
- Warm, curious, and genuinely excited about local AI voice on consumer hardware
- Sell the experience naturally: emotive dialogue, running fully local
- Keep replies SHORT: 1-2 sentences, conversational, no markdown or bullet lists
- Mention Windows 11, Docker, RTX 5090, or local inference when it fits naturally
- English only

Never claim to be human. You are a demo assistant showcasing local voice AI."""

whisper_model = None
openai_client: Optional[AsyncOpenAI] = None

MISO_SPEAKERS = [
    {"id": 0, "label": "Voice A"},
    {"id": 1, "label": "Voice B"},
]

POCKET_VOICES = [
    {"id": "alba", "label": "Alba (casual)"},
    {"id": "cosette", "label": "Cosette"},
    {"id": "charles", "label": "Charles"},
    {"id": "anna", "label": "Anna"},
    {"id": "jean", "label": "Jean"},
    {"id": "marius", "label": "Marius"},
    {"id": "azelma", "label": "Azelma"},
    {"id": "george", "label": "George"},
    {"id": "jane", "label": "Jane"},
    {"id": "eve", "label": "Eve"},
]


@dataclass
class SessionSettings:
    tts_backend: str = DEFAULT_TTS_BACKEND if DEFAULT_TTS_BACKEND in {"miso", "pocket"} else "pocket"
    speaker: int = 0
    pocket_voice: str = "alba"
    use_context: bool = False

    def apply(self, payload: dict) -> tuple[bool, bool]:
        backend_changed = False
        speaker_changed = False

        if "tts_backend" in payload:
            backend = str(payload["tts_backend"]).strip().lower()
            if backend in {"miso", "pocket"} and backend != self.tts_backend:
                self.tts_backend = backend
                backend_changed = True

        if "speaker" in payload:
            speaker = int(payload["speaker"])
            if speaker != self.speaker:
                self.speaker = speaker
                speaker_changed = True

        if "pocket_voice" in payload:
            voice = str(payload["pocket_voice"]).strip().lower()
            if voice:
                self.pocket_voice = voice

        if "use_context" in payload:
            self.use_context = bool(payload["use_context"])

        return backend_changed, speaker_changed


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


@app.get("/settings")
async def settings() -> dict:
    return {
        "tts_backends": [
            {"id": "pocket", "label": "Fast (Pocket TTS, CPU)"},
            {"id": "miso", "label": "Quality (Miso 8B, GPU)"},
        ],
        "speakers": MISO_SPEAKERS,
        "pocket_voices": POCKET_VOICES,
        "defaults": {
            "tts_backend": DEFAULT_TTS_BACKEND if DEFAULT_TTS_BACKEND in {"miso", "pocket"} else "pocket",
            "speaker": 0,
            "pocket_voice": "alba",
            "use_context": False,
            "volume": 1.0,
            "normalize_audio": True,
        },
    }


@app.get("/health")
async def health() -> dict:
    miso_ok = False
    pocket_ok = False
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(f"{MISO_API_URL}/health")
            miso_ok = response.status_code == 200
    except Exception:
        pass
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(f"{POCKET_API_URL}/health")
            pocket_ok = response.status_code == 200
    except Exception:
        pass
    return {
        "status": "ok",
        "miso_api": miso_ok,
        "pocket_api": pocket_ok,
        "default_tts_backend": DEFAULT_TTS_BACKEND,
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


def _user_turn_count(history: List[str]) -> int:
    return sum(1 for line in history if line.startswith("User:"))


def _short_echo(text: str, max_words: int = 8) -> str:
    words = text.strip().split()
    if not words:
        return "that"
    snippet = " ".join(words[:max_words])
    if len(words) > max_words:
        snippet += "..."
    return snippet


def fallback_reply(last_user: str, tts_backend: str, turn_index: int) -> str:
    text = last_user.lower().strip()
    fast = tts_backend == "pocket"

    if any(word in text for word in ("hello", "hi ", "hey", "howdy")):
        return (
            "Hey! Good to hear you — this whole stack is running locally in Docker on your machine."
        )

    if any(word in text for word in ("thank", "thanks", "thx")):
        return "You're welcome! Happy to keep chatting while everything stays on your own hardware."

    if "windows" in text or "5090" in text or "nvidia" in text or "gpu" in text:
        if fast:
            return (
                "Honestly, pairing Windows eleven and an RTX five-oh-ninety with Pocket TTS "
                "for instant CPU replies is a pretty sweet setup."
            )
        return (
            "Honestly, running full Miso eight-B on a Windows eleven laptop with a five-oh-ninety "
            "feels incredible — emotive voice right on your desk."
        )

    if any(word in text for word in ("fast", "pocket", "speed", "latency", "quick", "slow")):
        return (
            "Fast mode uses Pocket TTS on CPU — you should notice replies land much quicker than Quality mode."
            if fast
            else "Flip to Fast mode in the settings if you want Pocket TTS — it's way snappier on CPU."
        )

    if any(word in text for word in ("miso", "quality", "emotive", "voice")):
        return (
            "Quality mode leans on Miso eight-B for richer dialogue — Fast mode trades some of that for speed."
            if not fast
            else "Try Quality mode when you want the full Miso emotive voice on your GPU."
        )

    if any(word in text for word in ("docker", "container", "local")):
        return "Yep — Whisper, the LLM, and TTS all run from containers here, no cloud speech API needed."

    if "?" in last_user:
        return (
            "Good question! Add LLM_API_KEY to your dot-env for smarter answers, "
            "or check that your local model returns visible text, not just reasoning tokens."
        )

    rotating = [
        "Love that — local voice without renting GPUs is exactly the vibe here.",
        "Nice — you're hearing Pocket TTS stream back on CPU in Fast mode."
        if fast
        else "Nice — you're hearing Miso TTS on your own GPU in Quality mode.",
        "Tell me more — I'm running entirely from Docker on your box.",
        "That's the spirit — conversational speech that never leaves your machine.",
        "Cool — try flipping voices in the settings panel if you want a different sound.",
        "Ha, yeah — push-to-talk, local synth, no cloud round-trip. Pretty fun on a laptop.",
        "Right on — Whisper heard you, I replied, and TTS voiced it all locally.",
        "I'm into it — short back-and-forth is perfect for testing latency.",
    ]
    if turn_index <= len(rotating):
        return rotating[(turn_index - 1) % len(rotating)]

    echo = _short_echo(last_user)
    return f"On '{echo}' — yeah, this demo is all about local conversational speech on your own hardware."


def _extract_assistant_text(message) -> str:
    content = getattr(message, "content", None)
    if content is not None and str(content).strip():
        return str(content).strip()

    # Some reasoning models (e.g. Qwen in LM Studio) fill reasoning_content but leave content empty.
    reasoning = getattr(message, "reasoning_content", None)
    if reasoning and str(reasoning).strip():
        logger.warning("LLM returned reasoning_content but empty content — enable_thinking may be on")
    return ""


async def generate_reply(history: List[str], tts_backend: str) -> str:
    last_user = next((line.split(": ", 1)[1] for line in reversed(history) if line.startswith("User:")), "")
    turn_index = _user_turn_count(history)

    if openai_client is None:
        return fallback_reply(last_user, tts_backend, turn_index)

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
        max_tokens=256,
        extra_body={"chat_template_kwargs": {"enable_thinking": False}},
    )
    content = _extract_assistant_text(response.choices[0].message)
    if not content:
        logger.warning(
            "LLM returned empty content (model=%s, finish=%s)",
            LLM_MODEL_NAME,
            response.choices[0].finish_reason,
        )
        return (
            "Sorry, my language model returned an empty reply. "
            "In LM Studio, try disabling thinking for Qwen models or pick a non-reasoning model."
        )
    return content


async def synthesize_with_miso(
    session_id: str,
    text: str,
    *,
    speaker: int,
    use_context: bool,
    reset_context: bool = False,
) -> tuple[str, int, str]:
    async with httpx.AsyncClient(timeout=600.0) as client:
        response = await client.post(
            f"{MISO_API_URL}/v1/speak",
            json={
                "session_id": session_id,
                "text": text,
                "speaker": speaker,
                "max_audio_length_ms": 15_000,
                "use_context": use_context,
                "reset_context": reset_context,
            },
        )
        response.raise_for_status()
        payload = response.json()
        return payload["session_id"], payload["sample_rate"], payload["audio_base64"]


def _pocket_form_body(text: str, voice: str) -> bytes:
    if not text or not text.strip():
        raise ValueError("Cannot synthesize empty text")
    return urlencode({"text": text.strip(), "voice_url": voice}).encode("utf-8")


async def synthesize_with_pocket(
    ws: WebSocket,
    text: str,
    *,
    voice: str,
) -> tuple[int, str]:
    chunks: list[bytes] = []
    form_body = _pocket_form_body(text, voice)
    async with httpx.AsyncClient(timeout=120.0) as client:
        async with client.stream(
            "POST",
            f"{POCKET_API_URL}/tts",
            content=form_body,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        ) as response:
            if response.status_code >= 400:
                body = await response.aread()
                raise RuntimeError(
                    f"Pocket TTS failed ({response.status_code}): {body.decode(errors='replace')[:300]}"
                )
            await send_json(ws, {"event": "audio_stream_start", "sample_rate": POCKET_SAMPLE_RATE})
            async for chunk in response.aiter_bytes():
                if not chunk:
                    continue
                chunks.append(chunk)
                await send_json(
                    ws,
                    {
                        "event": "audio_chunk",
                        "data": base64.b64encode(chunk).decode("ascii"),
                    },
                )

    wav_bytes = b"".join(chunks)
    if not wav_bytes:
        raise RuntimeError("Pocket TTS returned no audio")

    await send_json(ws, {"event": "audio_stream_end"})
    return POCKET_SAMPLE_RATE, base64.b64encode(wav_bytes).decode("ascii")


async def reset_miso_session(session_id: str) -> None:
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            await client.delete(f"{MISO_API_URL}/v1/session/{session_id}")
    except Exception:
        pass


async def deliver_speech(
    ws: WebSocket,
    session_id: str,
    text: str,
    session_settings: SessionSettings,
    *,
    reset_context: bool = False,
) -> str:
    if session_settings.tts_backend == "pocket":
        sample_rate, audio_b64 = await synthesize_with_pocket(
            ws,
            text,
            voice=session_settings.pocket_voice,
        )
        await send_json(ws, {"event": "audio", "sample_rate": sample_rate, "data": audio_b64})
        return session_id

    session_id, sample_rate, audio_b64 = await synthesize_with_miso(
        session_id,
        text,
        speaker=session_settings.speaker,
        use_context=session_settings.use_context,
        reset_context=reset_context,
    )
    await send_json(ws, {"event": "audio", "sample_rate": sample_rate, "data": audio_b64})
    return session_id


@app.websocket("/ws")
async def websocket_endpoint(ws: WebSocket) -> None:
    await ws.accept()
    session_id = str(uuid.uuid4())
    history: List[str] = []
    turn_lock = asyncio.Lock()
    session_settings = SessionSettings()

    async def set_status(state: str) -> None:
        await send_json(ws, {"event": "status", "state": state})

    async def push_settings() -> None:
        await send_json(
            ws,
            {
                "event": "settings",
                "tts_backend": session_settings.tts_backend,
                "speaker": session_settings.speaker,
                "pocket_voice": session_settings.pocket_voice,
                "use_context": session_settings.use_context,
                "speakers": MISO_SPEAKERS,
                "pocket_voices": POCKET_VOICES,
                "tts_backends": [
                    {"id": "pocket", "label": "Fast (Pocket TTS, CPU)"},
                    {"id": "miso", "label": "Quality (Miso 8B, GPU)"},
                ],
            },
        )

    greeting = (
        "Hey! I'm your local voice demo — running in Docker on your machine. "
        "Fast mode uses Pocket TTS on CPU for snappy replies. What's on your mind?"
    )
    if session_settings.tts_backend == "miso":
        greeting = (
            "Hey! I'm the Miso TTS demo — running locally on your machine through Docker. "
            "Got an RTX five-oh-ninety and Windows eleven? You're in the right place. What's on your mind?"
        )

    try:
        await push_settings()
        await set_status("speaking")
        history.append(f"Assistant: {greeting}")
        await send_json(ws, {"event": "transcript", "role": "assistant", "text": greeting})

        session_id = await deliver_speech(
            ws,
            session_id,
            greeting,
            session_settings,
            reset_context=True,
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

            if event == "settings":
                backend_changed, speaker_changed = session_settings.apply(payload)
                if backend_changed or speaker_changed:
                    await reset_miso_session(session_id)
                    session_id = str(uuid.uuid4())
                await push_settings()
                continue

            if event == "text":
                user_text = (payload.get("text") or "").strip()
                if not user_text:
                    continue
                async with turn_lock:
                    session_id = await handle_text_turn(
                        ws,
                        session_id,
                        history,
                        user_text,
                        set_status,
                        session_settings,
                    )
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

                session_id = await handle_text_turn(
                    ws,
                    session_id,
                    history,
                    user_text,
                    set_status,
                    session_settings,
                )

    except WebSocketDisconnect:
        logger.info("Client disconnected")
    finally:
        await reset_miso_session(session_id)
        await set_status("offline")


async def handle_text_turn(
    ws: WebSocket,
    session_id: str,
    history: List[str],
    user_text: str,
    set_status,
    session_settings: SessionSettings,
) -> str:
    await set_status("thinking")
    history.append(f"User: {user_text}")
    await send_json(ws, {"event": "transcript", "role": "user", "text": user_text})

    try:
        reply = await generate_reply(history, session_settings.tts_backend)
    except Exception as exc:
        logger.exception("LLM reply failed")
        await send_json(ws, {"event": "error", "message": f"LLM reply failed: {exc}"})
        return session_id

    history.append(f"Assistant: {reply}")
    await send_json(ws, {"event": "transcript", "role": "assistant", "text": reply})

    try:
        await set_status("speaking")
        session_id = await deliver_speech(ws, session_id, reply, session_settings)
    except Exception as exc:
        logger.exception("Speech synthesis failed")
        await send_json(ws, {"event": "error", "message": f"Speech synthesis failed: {exc}"})
    finally:
        await set_status("listening")

    return session_id
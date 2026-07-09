# ADR-0006: Web conversational demo architecture

**Status:** Accepted  
**Date:** 2026-07-09

## Context

Users want a Sesame CSM-style browser demo: speak to an assistant, hear emotive
Miso TTS replies, ideally entirely from the Docker stack. MisoTTS is TTS-only —
it does not transcribe speech or generate dialogue text.

## Decision

Split into two services:

| Service | Role | Hardware |
|---------|------|----------|
| `miso-api` | Keeps MisoTTS loaded; `POST /v1/speak` with session context | GPU |
| `web` | FastAPI + WebSocket UI; Whisper STT; OpenAI-compatible LLM | CPU |

Pipeline per turn:

1. Browser captures mic audio (WebM) or typed text
2. `web` transcribes with **faster-whisper** (CPU, `base.en` default)
3. `web` calls configured **LLM** for short assistant reply text
4. `web` calls **`miso-api`** to synthesize speech with conversation `Segment` context
5. Browser plays returned WAV (24 kHz)

`MISO_API_URL` env allows web on a separate host from the GPU stack.

## Consequences

**Positive**

- Showcases Miso conversational continuity across turns
- Self-hosted STT without Google Cloud or Deepgram
- LLM optional (fallback replies if `LLM_API_KEY` unset)
- Inspired by HappyMonkeyAI/voice-assistant orb UX, simplified for demo

**Negative**

- Not low-latency streaming TTS — batch synthesis per turn
- `miso-api` and CLI `demo`/`generate` should not run concurrently on one GPU
- First `miso-api` start loads ~16 GB model; Whisper adds CPU RAM
- Push-to-talk, not continuous streaming STT

**Alternatives considered**

- Google Cloud STT — rejected for self-hosted goal
- Browser Web Speech API only — optional future; Whisper chosen for Docker-only path
- Cartesia/Deepgram TTS — rejected; Miso TTS is the point of the demo
# miso-tts-docker

Unofficial Docker Compose setup for running [Miso TTS 8B](https://github.com/MisoLabsAI/MisoTTS) locally on NVIDIA GPUs — especially **Windows**, **Docker Desktop**, and **RTX 50-series (Blackwell)** cards.

This project is **not affiliated with Miso Labs**. It wraps the upstream inference code with GPU-ready containers, Hugging Face caching, and Windows-friendly launchers.

## Features

- **Docker Compose** with NVIDIA GPU passthrough
- **PyTorch 2.11 + CUDA 12.8** for RTX 5090 / Blackwell (`sm_120`)
- **Full bfloat16** model by default (~24 GB VRAM)
- **Persistent Hugging Face cache** via named Docker volumes
- **Preflight checks** for gated Llama 3.2 tokenizer access
- **`soundfile` audio I/O patch** for PyTorch 2.11 (`torchcodec` not required)
- **Windows `.cmd` launchers** (no PowerShell execution-policy changes needed)
- **Web voice demo** with Whisper STT, optional LLM replies, and dual TTS backends
- **Fast mode** — [Pocket TTS](https://github.com/kyutai-labs/pocket-tts) on CPU for low-latency replies
- **HTTPS (Caddy)** for microphone access from LAN devices

## Requirements

| Item | Notes |
|------|-------|
| **GPU** | NVIDIA with **≥24 GB VRAM** recommended for Miso Quality mode |
| **Docker** | Docker Desktop (Windows) or Docker Engine (Linux) |
| **NVIDIA Container Toolkit** | GPU passthrough inside containers (Quality mode only) |
| **Disk** | ~40 GB free for first-run Miso model downloads |
| **Hugging Face account** | Token + accepted license for [meta-llama/Llama-3.2-1B](https://huggingface.co/meta-llama/Llama-3.2-1B) |

Fast mode (Pocket TTS) runs speech synthesis on **CPU** — no GPU required for TTS.

## Quick start

### 1. Clone and configure

```cmd
git clone https://github.com/HappyMonkeyAI/miso-tts-docker.git
cd miso-tts-docker
copy .env.example .env
```

Edit `.env` and set your Hugging Face token:

```env
HF_TOKEN=hf_your_token_here
```

Accept the Llama license while logged into the same HF account:
https://huggingface.co/meta-llama/Llama-3.2-1B

Verify access:

```cmd
check-access.cmd
```

### 2. Build

```cmd
build.cmd
```

First build clones [MisoLabsAI/MisoTTS](https://github.com/MisoLabsAI/MisoTTS) and installs dependencies (~15–25 min depending on network).

### 3. Run the CLI demo

```cmd
run-demo.cmd
```

Output: `output\full_conversation.wav`

First inference run downloads ~30–40 GB into the `miso-hf-cache` Docker volume. Later runs reuse the cache.

## Web conversational demo

Browser demo: hold-to-talk or type messages, Whisper transcribes locally, an LLM writes short replies, and TTS voices the assistant.

### Fast mode (recommended to start)

Pocket TTS on CPU — snappy replies, no GPU needed for speech:

```cmd
run-web-fast.cmd
```

### Fast + Quality (A/B both engines)

```cmd
run-web.cmd
```

Starts Pocket TTS (CPU) and Miso 8B (GPU). Switch engines in the web UI.

### HTTPS and microphone access

Browsers require a **secure context** for microphone access when not using `http://localhost`. The stack includes Caddy on port **8443** with a self-signed dev certificate.

1. Set your LAN IP in `.env` (for phone/tablet access on your network):

   ```env
   DEV_CERT_IP=192.168.5.157
   ```

2. Generate or refresh certs:

   ```cmd
   scripts\gen-dev-certs.cmd --force
   ```

3. Open:

   - **This PC:** https://localhost:8443
   - **LAN devices:** https://192.168.5.157:8443 (use your `DEV_CERT_IP`)

   Accept the browser security warning once per device.

Plain HTTP on port 8000 still works for typed messages on localhost only.

### LLM for smarter replies

Two different keys in `.env`:

| Variable | Purpose |
|----------|---------|
| `HF_TOKEN` | Download Miso/Pocket models and Llama tokenizer |
| `LLM_API_KEY` | Generate conversational **text** replies (before TTS) |

Without `LLM_API_KEY`, the demo uses rotating fallback replies (chat works, but not truly conversational).

**OpenRouter (default):**

```env
LLM_BASE_URL=https://openrouter.ai/api/v1
LLM_API_KEY=sk-or-v1-your-key-here
LLM_MODEL_NAME=google/gemma-2-9b-it:free
```

Get a key at https://openrouter.ai/settings/keys

**LM Studio (local):**

```env
LLM_BASE_URL=http://host.docker.internal:1234/v1
LLM_API_KEY=dummy-key
LLM_MODEL_NAME=your-model-id
```

Enable the **OpenAI-compatible** server in LM Studio on port **1234**. The path must be `/v1` — **not** `/api/v1` (LM Studio is not OpenRouter). From inside Docker on Windows, use `host.docker.internal` instead of your LAN IP.

**Ollama (local):**

```env
LLM_BASE_URL=http://host.docker.internal:11434/v1
LLM_API_KEY=ollama
LLM_MODEL_NAME=llama3.2
```

After changing `.env`, recreate the web container (restart alone does not reload env):

```cmd
docker compose up -d web
```

Confirm at http://localhost:8000/health — `"llm_configured": true`.

### Voice settings (web UI)

| Control | Description |
|---------|-------------|
| **TTS engine** | Fast (Pocket CPU) or Quality (Miso GPU) |
| **Pocket voice** | Alba, Cosette, Charles, and others |
| **Miso speaker** | Voice A / Voice B |
| **Volume / normalize** | Playback level and loudness normalization |
| **Voice continuity** | Miso only — carries tone across turns (can drift) |

### Remote GPU host

Run the web UI on another machine while TTS stays on your GPU box:

```env
MISO_API_URL=http://YOUR_GPU_HOST:8080
```

## Commands

| Command | Description |
|---------|-------------|
| `build.cmd` | Build the Miso TTS Docker image |
| `check-access.cmd` | Verify HF token and Llama tokenizer access |
| `run-demo.cmd` | Multi-turn CLI conversation demo |
| `run-generate.cmd "Your text"` | Generate speech from custom text |
| `run-generate.cmd "Next line" out.wav prompt.wav "prompt transcript"` | Voice continuation |
| `run-web-fast.cmd` | Web demo — Pocket TTS + HTTPS (CPU, no GPU for speech) |
| `run-web.cmd` | Web demo — Fast + Quality backends + HTTPS |
| `scripts\gen-dev-certs.cmd` | Generate self-signed TLS certs for HTTPS |
| `scripts\gen-dev-certs.cmd --force` | Regenerate certs after IP change |
| `shell.cmd` | Interactive shell inside the Miso container |

PowerShell scripts (`.ps1`) are also provided if your execution policy allows them.

## Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `HF_TOKEN` | — | Hugging Face token (required for Miso) |
| `MISO_TTS_8B_MODEL` | `MisoLabs/MisoTTS` | Model repo or local path |
| `TTS_BACKEND` | `pocket` | Default web engine: `pocket` or `miso` |
| `MISO_API_URL` | `http://miso-api:8080` | Miso GPU TTS API |
| `POCKET_API_URL` | `http://pocket-api:8090` | Pocket CPU TTS API |
| `WEB_PORT` | `8000` | HTTP port (localhost typing only) |
| `WEB_HTTPS_PORT` | `8443` | HTTPS port (microphone access) |
| `DEV_CERT_IP` | — | LAN IP added to self-signed TLS cert |
| `LLM_BASE_URL` | `https://openrouter.ai/api/v1` | OpenAI-compatible LLM endpoint |
| `LLM_API_KEY` | — | LLM API key for smart replies |
| `LLM_MODEL_NAME` | `google/gemma-2-9b-it:free` | Model name for replies |

For lower VRAM (~11–12 GB), use the community INT4 build:

```env
MISO_TTS_8B_MODEL=droyster/MisoTTS-8B-torchao-int4
```

## Architecture

```
Browser (HTTPS :8443)
    → Caddy (TLS)
    → web (Whisper STT + LLM + WebSocket UI)
        → pocket-api (Fast mode, CPU, streaming TTS)
        → miso-api  (Quality mode, GPU, Miso 8B)
```

## Troubleshooting

### `403` / gated repo for `meta-llama/Llama-3.2-1B`

Your HF account must accept the Llama license. Run `check-access.cmd` to confirm.

### Microphone blocked in browser

Use **HTTPS** (`https://localhost:8443` or `https://YOUR_LAN_IP:8443`), not plain HTTP over a network IP. Run `scripts\gen-dev-certs.cmd --force` after setting `DEV_CERT_IP`.

### Same canned reply every time

Set `LLM_API_KEY` in `.env`, then `docker compose up -d web` (not just `restart`).

### `TorchCodec is required`

Rebuild after pulling latest, or ensure `scripts/patch_torchaudio.py` is mounted. The demo uses `scripts/run_demo.py` which applies the patch automatically.

### PowerShell scripts blocked

Use the `.cmd` launchers instead.

### `sm_120 is not compatible with PyTorch`

This image pins **PyTorch 2.11 + CUDA 12.8**. Rebuild with `build.cmd`. Do not downgrade to PyTorch 2.4.

### LLM key not picked up after editing `.env`

`docker compose restart web` does not reload environment variables. Use:

```cmd
docker compose up -d web
```

## Project docs

- [CONTEXT.md](CONTEXT.md) — operating manual for contributors and agents
- [HERMES.md](HERMES.md) — agent workflow rules
- [docs/adr/](docs/adr/) — architecture decision records
- [research/](research/) — external references and notes

## Upstream

- **Miso inference:** [MisoLabsAI/MisoTTS](https://github.com/MisoLabsAI/MisoTTS)
- **Miso weights:** [MisoLabs/MisoTTS](https://huggingface.co/MisoLabs/MisoTTS)
- **Pocket TTS:** [kyutai-labs/pocket-tts](https://github.com/kyutai-labs/pocket-tts)
- **Website:** [misolabs.ai](https://misolabs.ai)

## License

This wrapper is [MIT](LICENSE). Miso TTS inference code and weights are subject to the [upstream license](https://github.com/MisoLabsAI/MisoTTS/blob/main/LICENSE). See [NOTICE.md](NOTICE.md).
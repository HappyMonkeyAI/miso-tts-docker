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

## Requirements

| Item | Notes |
|------|-------|
| **GPU** | NVIDIA with **≥24 GB VRAM** recommended for full model |
| **Docker** | Docker Desktop (Windows) or Docker Engine (Linux) |
| **NVIDIA Container Toolkit** | GPU passthrough inside containers |
| **Disk** | ~40 GB free for first-run model downloads |
| **Hugging Face account** | Token + accepted license for [meta-llama/Llama-3.2-1B](https://huggingface.co/meta-llama/Llama-3.2-1B) |

## Quick start

### 1. Clone and configure

```cmd
git clone https://github.com/YOUR_USER/miso-tts-docker.git
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

### 3. Run the demo

```cmd
run-demo.cmd
```

Output: `output\full_conversation.wav`

First inference run downloads ~30–40 GB into the `miso-hf-cache` Docker volume. Later runs reuse the cache.

## Web conversational demo

Sesame-style browser demo: talk to an enthusiastic Miso assistant, with Whisper STT
and your choice of LLM for replies — voiced by Miso TTS on your GPU.

```cmd
run-web.cmd
```

Open **http://localhost:8000**, click **Start Conversation**, then hold **Hold to Talk**
or type a message.

Optional: set `LLM_API_KEY` in `.env` (OpenRouter, LM Studio, Ollama OpenAI shim).
Without it, built-in fallback replies still demo Miso TTS.

To run the web UI on another machine while the GPU stays local:

```env
MISO_API_URL=http://YOUR_GPU_HOST:8080
```

## Commands

| Command | Description |
|---------|-------------|
| `build.cmd` | Build the Docker image |
| `check-access.cmd` | Verify HF token and Llama tokenizer access |
| `run-demo.cmd` | Multi-turn conversation demo |
| `run-generate.cmd "Your text"` | Generate speech from custom text |
| `run-generate.cmd "Next line" out.wav prompt.wav "prompt transcript"` | Voice continuation |
| `run-web.cmd` | Start browser voice demo (`miso-api` + `web`) |
| `shell.cmd` | Interactive shell inside the container |

PowerShell scripts (`.ps1`) are also provided if your execution policy allows them.

## Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `HF_TOKEN` | — | Hugging Face token (required) |
| `MISO_TTS_8B_MODEL` | `MisoLabs/MisoTTS` | Model repo or local path |
| `MISO_API_URL` | `http://miso-api:8080` | GPU TTS API (for web demo) |
| `LLM_BASE_URL` / `LLM_API_KEY` | OpenRouter defaults | LLM for assistant replies |
| `WEB_PORT` | `8000` | Browser demo port |

For lower VRAM (~11–12 GB), use the community INT4 build:

```env
MISO_TTS_8B_MODEL=droyster/MisoTTS-8B-torchao-int4
```

## Troubleshooting

### `403` / gated repo for `meta-llama/Llama-3.2-1B`

Your HF account must accept the Llama license. Run `check-access.cmd` to confirm.

### `TorchCodec is required`

Rebuild after pulling latest, or ensure `scripts/patch_torchaudio.py` is mounted. The demo uses `scripts/run_demo.py` which applies the patch automatically.

### PowerShell scripts blocked

Use the `.cmd` launchers instead.

### `sm_120 is not compatible with PyTorch`

This image pins **PyTorch 2.11 + CUDA 12.8**. Rebuild with `build.cmd`. Do not downgrade to PyTorch 2.4.

## Project docs

- [CONTEXT.md](CONTEXT.md) — operating manual for contributors and agents
- [HERMES.md](HERMES.md) — agent workflow rules
- [docs/adr/](docs/adr/) — architecture decision records
- [research/](research/) — external references and notes

## Upstream

- **Inference code:** [MisoLabsAI/MisoTTS](https://github.com/MisoLabsAI/MisoTTS)
- **Model weights:** [MisoLabs/MisoTTS](https://huggingface.co/MisoLabs/MisoTTS)
- **Website:** [misolabs.ai](https://misolabs.ai)

## License

This wrapper is [MIT](LICENSE). Miso TTS inference code and weights are subject to the [upstream license](https://github.com/MisoLabsAI/MisoTTS/blob/main/LICENSE). See [NOTICE.md](NOTICE.md).
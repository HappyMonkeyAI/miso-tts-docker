# CONTEXT.md

Operating manual for **miso-tts-docker**. Read this before making changes.

## What this repo is

An **unofficial Docker wrapper** around [MisoLabsAI/MisoTTS](https://github.com/MisoLabsAI/MisoTTS). It does not fork or reimplement the model. It makes upstream inference runnable in containers on Windows/Linux with modern NVIDIA GPUs.

## Stack and runtime assumptions

| Layer | Choice | Why |
|-------|--------|-----|
| Base image | `pytorch/pytorch:2.11.0-cuda12.8-cudnn9-runtime` | RTX 50-series needs CUDA 12.8 + `sm_120` |
| Orchestration | Docker Compose | GPU, volumes, reproducible env |
| Upstream code | Cloned at **image build** from `MisoLabsAI/MisoTTS@main` | Avoid vendoring; track upstream |
| Default model | `MisoLabs/MisoTTS` bfloat16 | Best quality on 24 GB cards |
| Audio I/O | `soundfile` via `scripts/patch_torchaudio.py` | PyTorch 2.11 `torchaudio` defaults need `torchcodec` |
| HF auth | `HF_TOKEN` env → `HUGGING_FACE_HUB_TOKEN` | Gated Llama 3.2 tokenizer |

## Non-negotiable rules

1. **Do not claim affiliation with Miso Labs.**
2. **Do not commit** `.env`, tokens, `grok.txt`, generated `.wav` files, or the local `MisoTTS/` clone.
3. **Keep PyTorch 2.11 + cu128** unless a newer stable build explicitly supports Blackwell and passes a CUDA tensor smoke test.
4. **Re-pin PyTorch after pip installs** — `moshi`/`bitsandbytes` deps can downgrade torch silently.
5. **Mount `./scripts` read-only** in compose so launcher fixes work without rebuild (until baked into image).
6. **Preflight gated HF access** before long inference runs.

## Workflow protocols

### Adding a feature

1. Check upstream MisoTTS — can it be env/config only?
2. If Docker-specific, change `scripts/` or `Dockerfile`.
3. Update ADR if architectural.
4. Update README troubleshooting if user-facing.
5. Test: `check-access.cmd` → `run-demo.cmd` or `run-generate.cmd`.

### Upstream MisoTTS update

Rebuild image (`build.cmd`). Dockerfile clones `main` at build time. If `generator.py` patch fails, fix the Dockerfile `RUN python` patch block.

### Windows support

Prefer `.cmd` over `.ps1`. Many users have `Restricted` execution policy.

## Resolved architecture decisions

See [docs/adr/](docs/adr/). Summary:

- Docker Compose over native `uv` for portability
- Clone upstream at build, not git submodule
- `run_demo.py` wrapper applies torchaudio patch + preflight
- Named volumes for HF and torch caches
- Full bfloat16 default; INT4 via env var

## What not to do

- **Do not** route inference through LM Studio, Ollama, or GGUF — MisoTTS needs its native multi-codebook pipeline.
- **Do not** use PyTorch 2.4 base images on RTX 5090 — kernels will not run.
- **Do not** vendor the full MisoTTS git history in this repo.
- **Do not** remove the Llama tokenizer preflight — failures happen after a 30+ GB download.
- **Do not** assume `PYTHONSTARTUP` patches imports — it only runs in interactive mode.

## Patching upstream files

Only in Dockerfile at build time:

| File | Patch |
|------|-------|
| `generator.py` | Pass `HF_TOKEN` to `AutoTokenizer.from_pretrained` |

Runtime patches live in `scripts/` (mounted volume).

## Key paths

```
Dockerfile              # Image build, upstream clone, generator patch
docker-compose.yml      # GPU, volumes, services
scripts/
  entrypoint.sh         # demo | generate | shell
  miso_api.py           # GPU HTTP API for web demo (persistent model)
  preflight.py          # HF + Llama access check
  patch_torchaudio.py   # soundfile save/load
  run_demo.py           # Patched demo entry
  generate.py           # Custom text CLI
web/
  src/main.py           # WebSocket gateway, Whisper STT, LLM
  src/index.html        # Browser UI
*.cmd                   # Windows launchers
output/                 # Generated WAV (gitignored)
```

## Web demo notes

- Run `run-web.cmd` — starts `miso-api` (GPU) + `web` (CPU).
- Do not run `miso-api` and CLI `demo`/`generate` on the same GPU simultaneously.
- `MISO_API_URL` lets the web container target a remote GPU host.

## Hardware notes

- **24 GB** (RTX 3090/4090/5090 Laptop): full bfloat16 fits comfortably.
- **11–12 GB**: use `droyster/MisoTTS-8B-torchao-int4` via `MISO_TTS_8B_MODEL`.
- Laptop thermals: generation is bursty; expect fan noise under load.
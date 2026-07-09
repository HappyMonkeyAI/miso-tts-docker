# HERMES.md

Agent guide for **miso-tts-docker**. Complements [CONTEXT.md](CONTEXT.md).

## Role

Help maintain and extend this Docker wrapper. The model and inference logic live upstream — do not reimplement MisoTTS.

## Before editing

1. Read [CONTEXT.md](CONTEXT.md).
2. Check [docs/adr/](docs/adr/) for locked decisions.
3. Confirm whether the change belongs here or upstream.

## Repo workflow

| Task type | Approach |
|-----------|----------|
| User-facing fix | Patch `scripts/` or `Dockerfile`, update README troubleshooting |
| GPU/CUDA issue | Verify with `docker run --gpus all miso-tts:local python -c "..."` smoke test |
| HF auth issue | `scripts/preflight.py` and `check-access.cmd` first |
| Upstream API change | Update Dockerfile clone patch block |

## Testing checklist

```cmd
check-access.cmd
run-demo.cmd
run-generate.cmd "Short test sentence."
```

Confirm `output\*.wav` is created. Do not commit WAV files.

## Documentation duties

| Change | Update |
|--------|--------|
| Architecture | New ADR in `docs/adr/` |
| External reference | `research/github-projects/` note |
| User-facing behavior | `README.md` |
| Contributor rules | `CONTEXT.md` |

Keep ADRs short: context, decision, consequences.

## Do not

- Commit secrets, `grok.txt`, or generated audio.
- Downgrade PyTorch without Blackwell smoke test.
- Add LM Studio / Ollama integration — out of scope.
- Expand scope into training, fine-tuning, or web UI unless explicitly requested.

## Preferred change size

Small, focused diffs. One concern per PR/commit:

- `fix: torchaudio save on pytorch 2.11`
- `docs: adr for hf cache volumes`
- `feat: optional int4 model env docs`

## When stuck

1. Read upstream [MisoTTS README](https://github.com/MisoLabsAI/MisoTTS).
2. Check container logs from `docker compose run`.
3. Verify GPU: `nvidia-smi` on host and inside container.
4. Record findings in `research/notes/` if exploratory.
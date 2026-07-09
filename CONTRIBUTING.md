# Contributing

Thanks for helping improve **miso-tts-docker**.

## Before you start

1. Read [CONTEXT.md](CONTEXT.md) and [HERMES.md](HERMES.md).
2. Search existing [ADRs](docs/adr/) — don't relitigate settled decisions without new evidence.

## Pull requests

- One logical change per PR.
- Update docs when behavior changes.
- Add an ADR for architectural decisions.
- Do not include `.env`, tokens, audio files, or private notes.

## Local verification

```cmd
build.cmd
check-access.cmd
run-demo.cmd
```

## Reporting issues

Include:

- GPU model and driver version
- `docker --version` and `docker compose version`
- Output of `check-access.cmd`
- Full error traceback
- Whether first run or cached weights

## Upstream bugs

If the issue is in MisoTTS inference itself (not Docker wiring), file upstream
at [MisoLabsAI/MisoTTS/issues](https://github.com/MisoLabsAI/MisoTTS/issues)
and link it here.
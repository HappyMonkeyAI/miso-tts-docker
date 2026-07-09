# ADR-0004: Hugging Face gated Llama tokenizer

**Status:** Accepted  
**Date:** 2026-07-08

## Context

MisoTTS uses `meta-llama/Llama-3.2-1B` only for its **tokenizer** (not weights).
The repo is gated. Without accepted license access, downloads fail with HTTP 403
**after** the ~33 GB `MisoLabs/MisoTTS` weights have already downloaded.

## Decision

1. Require `HF_TOKEN` in `.env`, passed as `HUGGING_FACE_HUB_TOKEN`
2. Patch `generator.py` at build to pass token into `AutoTokenizer.from_pretrained`
3. Run `scripts/preflight.py` before demo/generate — uses `HfApi.auth_check`
4. Ship `check-access.cmd` for host-side verification

## Consequences

**Positive**

- Fails fast with actionable instructions
- Avoids repeating large downloads on auth mistakes

**Negative**

- Users must create HF account and accept Llama license
- Token must be kept out of git (`.env` gitignored)

**Not viable**

- LM Studio local GGUF models — no HuggingFace tokenizer artifacts; wrong inference stack
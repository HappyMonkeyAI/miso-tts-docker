# MisoLabsAI/MisoTTS

**URL:** https://github.com/MisoLabsAI/MisoTTS  
**License:** Modified MIT (Kamino Learning / Miso Labs)  
**Last reviewed:** 2026-07-08

## Summary

Official inference code for Miso TTS 8B — a Sesame CSM-style RVQ transformer
with ~8B backbone and ~300M audio decoder. Generates Mimi audio codebooks from
text and optional audio context. English only.

## Stack

- Python 3.10+, `uv` or pip
- PyTorch 2.4 (upstream pin)
- `moshi`, `transformers`, `silentcipher`, `torchao`

## Relevance to miso-tts-docker

This is the **core dependency**. We clone it at Docker build and apply minimal
patches (HF token for Llama tokenizer). All inference logic stays upstream.

## Cherry-pick

- `run_misotts.py` demo conversation flow
- `generator.load_miso_8b()` API
- `Segment` type for voice continuation
- Watermarking defaults (SilentCipher)

## Avoid

- Copying the repo into our git history
- Re-pinning torch to 2.4 on RTX 50-series
- Expecting GGUF/llama.cpp compatibility

## Open questions

- Will upstream add official Docker support?
- Will upstream adopt PyTorch 2.11+ for Blackwell natively?
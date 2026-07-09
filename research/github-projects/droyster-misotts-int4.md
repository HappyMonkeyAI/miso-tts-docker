# droyster/MisoTTS-8B-torchao-int4

**URL:** https://huggingface.co/droyster/MisoTTS-8B-torchao-int4  
**License:** Per model card (community quant of upstream)  
**Last reviewed:** 2026-07-08

## Summary

Community INT4 weight-only quant using torchao. Drops VRAM from ~24 GB to
~11–12 GB while keeping MisoTTS's native Python inference pipeline.

## Stack

- Same inference code as upstream MisoTTS
- torchao INT4 weights on Hugging Face

## Relevance to miso-tts-docker

Optional via `MISO_TTS_8B_MODEL` env var for users without 24 GB VRAM. Not the
default — full bfloat16 is recommended when VRAM allows.

## Cherry-pick

- Document as env-var swap in README
- No separate Docker image needed

## Avoid

- Making INT4 the default (quality tradeoff on capable hardware)
- Expecting it to work without upstream inference code

## Open questions

- Does INT4 need a different loader path (`load_miso_8b_torchao_int4`) on latest upstream?
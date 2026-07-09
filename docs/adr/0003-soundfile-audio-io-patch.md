# ADR-0003: soundfile patch for torchaudio I/O

**Status:** Accepted  
**Date:** 2026-07-08

## Context

PyTorch 2.11's `torchaudio.save()` and `torchaudio.load()` default to a
`torchcodec` backend. The runtime image does not include `torchcodec`, causing
inference to fail **after** successful generation when writing WAV output.

## Decision

Provide `scripts/patch_torchaudio.py` that replaces `torchaudio.save` and
`torchaudio.load` with `soundfile` implementations. Apply the patch from:

- `scripts/run_demo.py` (demo)
- `scripts/generate.py` (custom generation)

`soundfile` is already installed transitively via MisoTTS dependencies.

## Consequences

**Positive**

- Demo completes end-to-end without adding `torchcodec`
- Patch is small and testable in isolation

**Negative**

- Monkey-patch approach is fragile if torchaudio API changes
- `watermarking.py` still uses unpatched `torchaudio.load` on CLI paths not used by demo

**Alternatives considered**

- Install `torchcodec` — rejected pending CUDA compatibility verification
- Pin older torchaudio behavior — rejected; base image ships 2.11
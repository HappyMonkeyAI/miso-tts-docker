# ADR-0002: PyTorch 2.11 + CUDA 12.8 for Blackwell GPUs

**Status:** Accepted  
**Date:** 2026-07-08

## Context

MisoTTS upstream pins `torch==2.4.0`. On RTX 5090 Laptop (`sm_120` / Blackwell),
PyTorch 2.4 reports CUDA capability mismatch and fails with:

```
CUDA error: no kernel image is available for execution on the device
```

Blackwell requires CUDA 12.8+ and PyTorch builds with `sm_120` support (2.7+;
we use 2.11.0 stable).

## Decision

Base the image on `pytorch/pytorch:2.11.0-cuda12.8-cudnn9-runtime` and
**force-reinstall** `torch==2.11.0` + `torchaudio==2.11.0` from the `cu128`
wheel index after installing MisoTTS dependencies.

## Consequences

**Positive**

- RTX 50-series GPUs run CUDA kernels correctly
- Stable release channel (not nightly)

**Negative**

- Diverges from upstream `torch==2.4.0` pin — compatibility must be watched
- `pip install` of `moshi`/`bitsandbytes` can silently downgrade torch; re-pin step is mandatory
- Images built for CUDA 12.8 may not run on very old NVIDIA driver stacks

**Verification**

```bash
docker run --rm --gpus all miso-tts:local python -c \
  "import torch; x=torch.randn(2,2,device='cuda'); print(x.sum())"
```
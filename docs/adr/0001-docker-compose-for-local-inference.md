# ADR-0001: Docker Compose for local inference

**Status:** Accepted  
**Date:** 2026-07-08

## Context

MisoTTS upstream documents a native `uv` + Python 3.10 workflow. Contributors
target Linux/macOS shells. Windows users with NVIDIA GPUs face additional friction:
CUDA toolkit alignment, dependency isolation, and ~40 GB of cached model artifacts.

## Decision

Package inference as a **Docker Compose** project with:

- `gpus: all` for NVIDIA passthrough
- Named volumes `miso-hf-cache` and `miso-torch-cache`
- Bind mounts for `output/`, `data/`, and `scripts/`
- Windows `.cmd` launchers alongside optional `.ps1` scripts

## Consequences

**Positive**

- Reproducible environment across Windows and Linux
- Model downloads persist across container restarts
- No host Python/CUDA version conflicts

**Negative**

- Requires Docker Desktop + NVIDIA container support on Windows
- Image build is large (~25 GB) and slow on first build
- Not ideal for users who cannot use Docker

**Alternatives considered**

- Native `uv` only — rejected as primary path; documented upstream instead
- Single `docker run` without Compose — rejected; volumes and services are clearer in Compose
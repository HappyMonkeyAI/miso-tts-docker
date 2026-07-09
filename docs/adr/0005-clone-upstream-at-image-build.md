# ADR-0005: Clone upstream at image build

**Status:** Accepted  
**Date:** 2026-07-08

## Context

Early development vendored a full `MisoTTS/` git clone in the workspace. That is
unsuitable for a public wrapper repo: nested `.git`, license boundary confusion,
and stale upstream copies.

## Decision

During `docker build`, shallow-clone `MisoLabsAI/MisoTTS` at `main`:

```dockerfile
ARG MISOTTS_REPO=https://github.com/MisoLabsAI/MisoTTS.git
ARG MISOTTS_REF=main
RUN git clone --depth 1 --branch "${MISOTTS_REF}" ...
```

Apply Docker-specific patches (generator token pass) at build time. Keep
runtime-specific patches in mounted `scripts/`.

## Consequences

**Positive**

- Public repo contains only wrapper code
- Rebuild always picks up latest upstream unless `MISOTTS_REF` is pinned
- Clear separation: wrapper MIT, upstream modified MIT

**Negative**

- Build requires network access to GitHub
- Upstream breaking changes can break the Dockerfile patch step
- Offline builds need a pre-populated build context (not supported yet)

**Alternatives considered**

- Git submodule — rejected; extra clone steps for contributors
- Vendor copy in repo — rejected for publication
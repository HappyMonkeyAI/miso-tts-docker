# LM Studio local models — not a MisoTTS tokenizer source

**Date:** 2026-07-08

## Question

Can models in `~/.lmstudio` replace the gated `meta-llama/Llama-3.2-1B` download?

## Finding

LM Studio stores **GGUF** (and similar) weights for llama.cpp inference. MisoTTS
needs HuggingFace-format **tokenizer files** (`tokenizer.json`, etc.) loaded via
`transformers.AutoTokenizer`.

A scan of `C:\Users\steph\.lmstudio\models` found **no** `tokenizer.json`
artifacts. Models there are inference bundles for LM Studio, not HF tokenizer dirs.

## Conclusion

LM Studio paths are **not** a viable workaround for the Llama 3.2 gated tokenizer.
Users must accept the HF license or wait for approval.

## Alternative paths (not implemented)

- Manual download of tokenizer files into `data/` + `TOKENIZER_PATH` env (possible future ADR)
- Upstream bundling a non-gated tokenizer (upstream change)
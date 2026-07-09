# Architecture Decision Records

Durable decisions for **miso-tts-docker**. Newest last.

| ADR | Title | Status |
|-----|-------|--------|
| [0001](0001-docker-compose-for-local-inference.md) | Docker Compose for local inference | Accepted |
| [0002](0002-pytorch-cuda-12-8-for-blackwell-gpus.md) | PyTorch 2.11 + CUDA 12.8 for Blackwell GPUs | Accepted |
| [0003](0003-soundfile-audio-io-patch.md) | soundfile patch for torchaudio I/O | Accepted |
| [0004](0004-huggingface-gated-llama-tokenizer.md) | Hugging Face gated Llama tokenizer | Accepted |
| [0005](0005-clone-upstream-at-image-build.md) | Clone upstream at image build | Accepted |

## Format

Each ADR includes: **Context**, **Decision**, **Consequences**.

When reversing a decision, add a new ADR — do not silently delete old ones.
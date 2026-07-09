# Curated links

## Primary upstream

- [MisoLabsAI/MisoTTS](https://github.com/MisoLabsAI/MisoTTS) — inference code
- [MisoLabs/MisoTTS](https://huggingface.co/MisoLabs/MisoTTS) — model weights
- [misolabs.ai](https://misolabs.ai) — demos and blog
- [Miso TTS 8B blog post](https://misolabs.ai/blog/miso-tts-8b)

## Required gated dependency

- [meta-llama/Llama-3.2-1B](https://huggingface.co/meta-llama/Llama-3.2-1B) — tokenizer only
- [HF access tokens](https://huggingface.co/settings/tokens)

## Community quant (lower VRAM)

- [droyster/MisoTTS-8B-torchao-int4](https://huggingface.co/droyster/MisoTTS-8B-torchao-int4)

## GPU / PyTorch compatibility

- [PyTorch RTX 5090 discussion](https://discuss.pytorch.org/t/is-there-a-pytorch-build-that-supports-nvidia-rtx-5090-compute-capability-12-0-sm-120/223536)
- [Salad: PyTorch on RTX 5090](https://docs.salad.com/container-engine/tutorials/machine-learning/pytorch-rtx5090)
- [PyTorch Docker Hub](https://hub.docker.com/r/pytorch/pytorch)

## Not applicable (documented for clarity)

- LM Studio / Ollama / GGUF — wrong inference stack for MisoTTS multi-codebook audio
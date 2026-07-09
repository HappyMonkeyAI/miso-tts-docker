#!/usr/bin/env python3
"""Two-speaker demo: excitement about Miso TTS on Windows 11 + RTX 5090."""

import importlib.util
import os
import shutil

os.environ.setdefault("HF_HUB_ETAG_TIMEOUT", "60")
os.environ.setdefault("HF_HUB_DOWNLOAD_TIMEOUT", "60")
os.environ.setdefault("NO_TORCH_COMPILE", "1")


def _load_module(name: str, path: str):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Could not load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


_load_module("patch_torchaudio", "/app/scripts/patch_torchaudio.py")

if _load_module("preflight", "/app/scripts/preflight.py").main() != 0:
    raise SystemExit(1)

import torch
import torchaudio
from generator import Segment, load_miso_8b

CONVERSATION = [
    {
        "speaker_id": 0,
        "text": (
            "Okay, I have to say — running Miso TTS locally on this Windows 11 laptop "
            "feels unreal. Twenty-four gigs of VRAM on the RTX 5090 and we're actually "
            "generating speech right here on the desk."
        ),
    },
    {
        "speaker_id": 1,
        "text": (
            "Right? No cloud API, no rental GPU. Just Docker, an NVIDIA 5090, and the "
            "full eight-billion-parameter model in bfloat16. That is a wild setup for a laptop."
        ),
    },
    {
        "speaker_id": 0,
        "text": (
            "And the voices actually sound conversational. I fed it a couple of lines and "
            "it already feels emotive — like two people talking, not a robot reading a manual."
        ),
    },
    {
        "speaker_id": 1,
        "text": (
            "Exactly. Miso TTS was built for dialogue, and hearing it run on Windows with "
            "GPU passthrough is the part I'm most excited about. If this keeps up, local "
            "voice work on a 5090 laptop is genuinely practical."
        ),
    },
    {
        "speaker_id": 0,
        "text": (
            "Windows eleven, one GPU, one container — and we made a whole conversation out of text. "
            "I'm absolutely hooked on what we can do with this next."
        ),
    },
]


def main() -> None:
    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"Using device: {device}")

    model_source = os.environ.get("MISO_TTS_8B_MODEL", "MisoLabs/MisoTTS")
    print(f"Loading model: {model_source}")

    generator = load_miso_8b(device=device, model_path_or_repo_id=model_source)

    generated_segments: list[Segment] = []
    for utterance in CONVERSATION:
        print(f"[speaker {utterance['speaker_id']}] {utterance['text']}")
        audio = generator.generate(
            text=utterance["text"],
            speaker=utterance["speaker_id"],
            context=generated_segments,
            max_audio_length_ms=15_000,
        )
        generated_segments.append(
            Segment(
                text=utterance["text"],
                speaker=utterance["speaker_id"],
                audio=audio,
            )
        )

    all_audio = torch.cat([seg.audio for seg in generated_segments], dim=0)
    output_name = "windows_5090_excited.wav"
    torchaudio.save(output_name, all_audio.unsqueeze(0).cpu(), generator.sample_rate)

    dest = f"/app/output/{output_name}"
    shutil.move(output_name, dest)
    print(f"Saved {dest}")


if __name__ == "__main__":
    main()
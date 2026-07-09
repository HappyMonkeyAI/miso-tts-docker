#!/usr/bin/env python3
"""Generate speech from custom text using the MisoTTS Python API."""

import argparse
import importlib.util
import os

os.environ.setdefault("HF_HUB_ETAG_TIMEOUT", "60")
os.environ.setdefault("HF_HUB_DOWNLOAD_TIMEOUT", "60")
os.environ.setdefault("NO_TORCH_COMPILE", "1")

_spec = importlib.util.spec_from_file_location(
    "patch_torchaudio",
    "/app/scripts/patch_torchaudio.py",
)
_patch = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_patch)

import torch
import torchaudio
from generator import Segment, load_miso_8b


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate speech with MisoTTS 8B")
    parser.add_argument("--text", required=True, help="Text to synthesize")
    parser.add_argument("--speaker", type=int, default=0, help="Speaker id (default: 0)")
    parser.add_argument(
        "--output",
        default="/app/output/generated.wav",
        help="Output wav path",
    )
    parser.add_argument(
        "--max-audio-length-ms",
        type=int,
        default=10_000,
        help="Maximum audio length in milliseconds",
    )
    parser.add_argument(
        "--prompt-audio",
        default=None,
        help="Optional prompt wav for voice continuation",
    )
    parser.add_argument(
        "--prompt-text",
        default=None,
        help="Transcript for the prompt audio (required with --prompt-audio)",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    if bool(args.prompt_audio) != bool(args.prompt_text):
        raise SystemExit("Provide both --prompt-audio and --prompt-text, or neither.")

    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"Using device: {device}")

    model_source = os.environ.get("MISO_TTS_8B_MODEL", "MisoLabs/MisoTTS")
    print(f"Loading model: {model_source}")

    generator = load_miso_8b(device=device, model_path_or_repo_id=model_source)

    context: list[Segment] = []
    if args.prompt_audio:
        prompt_audio, sample_rate = torchaudio.load(args.prompt_audio)
        prompt_audio = torchaudio.functional.resample(
            prompt_audio.squeeze(0),
            orig_freq=sample_rate,
            new_freq=generator.sample_rate,
        )
        context = [
            Segment(
                speaker=args.speaker,
                text=args.prompt_text,
                audio=prompt_audio,
            )
        ]

    print(f"Generating: {args.text}")
    audio = generator.generate(
        text=args.text,
        speaker=args.speaker,
        context=context,
        max_audio_length_ms=args.max_audio_length_ms,
    )

    output_path = args.output
    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
    torchaudio.save(output_path, audio.unsqueeze(0).cpu(), generator.sample_rate)
    print(f"Saved {output_path}")


if __name__ == "__main__":
    main()
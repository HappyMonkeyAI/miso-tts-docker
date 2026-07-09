#!/usr/bin/env python3
import importlib.util
import os
import shutil
import sys


def _apply_torchaudio_patch() -> None:
    spec = importlib.util.spec_from_file_location(
        "patch_torchaudio",
        "/app/scripts/patch_torchaudio.py",
    )
    if spec is None or spec.loader is None:
        raise RuntimeError("Could not load patch_torchaudio.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)


_apply_torchaudio_patch()


def _load_preflight_main():
    spec = importlib.util.spec_from_file_location(
        "preflight",
        "/app/scripts/preflight.py",
    )
    if spec is None or spec.loader is None:
        raise RuntimeError("Could not load preflight.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.main


if _load_preflight_main() != 0:
    raise SystemExit(1)

import run_misotts

if __name__ == "__main__":
    run_misotts.main()
    if os.path.exists("full_conversation.wav"):
        shutil.move("full_conversation.wav", "/app/output/full_conversation.wav")
        print("Saved /app/output/full_conversation.wav")
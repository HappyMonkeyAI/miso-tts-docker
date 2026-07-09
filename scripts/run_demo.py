#!/usr/bin/env python3
import importlib.util
import os
import shutil
import sys

if "/app" not in sys.path:
    sys.path.insert(0, "/app")


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


import run_misotts

if __name__ == "__main__":
    run_misotts.main()
    if os.path.exists("full_conversation.wav"):
        shutil.move("full_conversation.wav", "/app/output/full_conversation.wav")
        print("Saved /app/output/full_conversation.wav")
"""Validate Hugging Face access before starting inference."""

import os
import sys

from huggingface_hub import HfApi
from huggingface_hub.errors import GatedRepoError, HfHubHTTPError

LLAMA_REPO = "meta-llama/Llama-3.2-1B"


def main() -> int:
    token = os.environ.get("HF_TOKEN") or os.environ.get("HUGGING_FACE_HUB_TOKEN")
    if not token:
        print("ERROR: HF_TOKEN is not set.")
        print("Copy .env.example to .env and add your Hugging Face token.")
        return 1

    api = HfApi(token=token)
    try:
        user = api.whoami()["name"]
    except HfHubHTTPError:
        print("ERROR: HF_TOKEN is invalid or expired.")
        print("Create a new token at https://huggingface.co/settings/tokens")
        return 1

    print(f"Hugging Face account: {user}")

    try:
        api.auth_check(LLAMA_REPO)
    except GatedRepoError:
        print()
        print("ERROR: Your account does not have access to the gated Llama tokenizer.")
        print(f"1. Open https://huggingface.co/{LLAMA_REPO}")
        print(f"2. Log in as {user}")
        print("3. Accept the license / request access (usually instant)")
        print("4. Re-run run-demo.cmd")
        return 1

    print(f"Access OK: {LLAMA_REPO}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
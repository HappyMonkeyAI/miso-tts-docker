#!/usr/bin/env bash
set -euo pipefail

if [[ -n "${HF_TOKEN:-}" ]]; then
  export HUGGING_FACE_HUB_TOKEN="${HF_TOKEN}"
fi

cmd="${1:-demo}"
shift || true

case "${cmd}" in
  demo|generate)
    if [[ -f /app/scripts/preflight.py ]]; then
      python /app/scripts/preflight.py || exit 1
    fi
    ;;
esac

case "${cmd}" in
  demo)
    python /app/scripts/run_demo.py
    ;;
  generate)
    python /app/scripts/generate.py "$@"
    ;;
  shell)
    exec bash
    ;;
  *)
    exec "${cmd}" "$@"
    ;;
esac
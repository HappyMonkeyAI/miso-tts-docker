# CUDA 12.8 + PyTorch 2.11 is required for RTX 5090 (sm_120 / Blackwell).
FROM pytorch/pytorch:2.11.0-cuda12.8-cudnn9-runtime

ARG MISOTTS_REPO=https://github.com/MisoLabsAI/MisoTTS.git
ARG MISOTTS_REF=main

ENV DEBIAN_FRONTEND=noninteractive \
    PYTHONUNBUFFERED=1 \
    HF_HUB_ETAG_TIMEOUT=60 \
    HF_HUB_DOWNLOAD_TIMEOUT=60 \
    NO_TORCH_COMPILE=1 \
    PIP_NO_CACHE_DIR=1

RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    libsndfile1 \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

RUN git clone --depth 1 --branch "${MISOTTS_REF}" "${MISOTTS_REPO}" /tmp/misotts \
    && cp /tmp/misotts/pyproject.toml /tmp/misotts/LICENSE /app/ \
    && cp /tmp/misotts/*.py /app/ \
    && rm -rf /tmp/misotts

COPY requirements-docker.txt ./

RUN python - <<'PY'
from pathlib import Path

path = Path("generator.py")
text = path.read_text()
old = "    tokenizer = AutoTokenizer.from_pretrained(tokenizer_name)"
new = (
    "    tokenizer = AutoTokenizer.from_pretrained(\n"
    "        tokenizer_name,\n"
    '        token=os.environ.get("HF_TOKEN") or os.environ.get("HUGGING_FACE_HUB_TOKEN"),\n'
    "    )"
)
if old not in text:
    raise SystemExit("generator.py patch failed")
path.write_text(text.replace(old, new))
PY

RUN pip install --break-system-packages --upgrade pip setuptools wheel \
    && pip install --break-system-packages -r requirements-docker.txt \
    && pip install --break-system-packages --force-reinstall \
       torch==2.11.0 torchaudio==2.11.0 \
       --index-url https://download.pytorch.org/whl/cu128 \
    && pip install --break-system-packages -e . --no-deps

COPY scripts/entrypoint.sh /usr/local/bin/entrypoint.sh
COPY scripts/patch_torchaudio.py /app/scripts/patch_torchaudio.py
COPY scripts/preflight.py /app/scripts/preflight.py
COPY scripts/run_demo.py /app/scripts/run_demo.py
COPY scripts/generate.py /app/scripts/generate.py
RUN sed -i 's/\r$//' /usr/local/bin/entrypoint.sh && chmod +x /usr/local/bin/entrypoint.sh

RUN mkdir -p /app/output /app/data

ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]
CMD ["demo"]
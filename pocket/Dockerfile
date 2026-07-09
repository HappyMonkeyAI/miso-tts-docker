FROM python:3.11-slim-bookworm

ENV DEBIAN_FRONTEND=noninteractive \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

RUN pip install --upgrade pip && pip install "pocket-tts>=2.1.0"

EXPOSE 8090

CMD ["pocket-tts", "serve", "--host", "0.0.0.0", "--port", "8090", "--quantize"]
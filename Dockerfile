# ── NutriVision Pro API — Dockerfile ──────────────────────────────────────────
# Build dari root project:
#   docker build -t nutrivision-api .
#   docker run -p 8000:8000 --env-file src/.env nutrivision-api
#
# Untuk EC2 tanpa GPU (t3.medium): pakai torch CPU di requirements-api.txt
# Untuk EC2 GPU (g4dn): ganti DEVICE="cuda:0" di src/inference.py

FROM python:3.11-slim

WORKDIR /app

# System deps untuk Pillow dan OpenCV headless yang dipakai Ultralytics
RUN apt-get update && apt-get install -y --no-install-recommends \
    libglib2.0-0 \
    libgl1 \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
# requirements-api.txt ada di src/ supaya tidak ketukar dengan requirements.txt notebook
COPY src/requirements-api.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code dan model
COPY src/ ./src/
COPY models/production/ ./models/production/

# Working dir = src/ supaya import relatif (inference, nutrition, dll) berjalan
WORKDIR /app/src

EXPOSE 8000

# Jalankan dengan 1 worker untuk MVP (model YOLO tidak thread-safe dengan multi-worker)
# Scale dengan multiple containers (ECS), bukan multiple workers per container
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]

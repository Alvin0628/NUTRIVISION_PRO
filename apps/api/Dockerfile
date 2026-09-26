# ── NutriVision Pro API — Dockerfile ──────────────────────────────────────────
# Build dari ROOT REPO (bukan dari apps/api/), karena model ada di models/
# yang sejajar dengan apps/, jadi build context harus mencakup keduanya:
#
#   docker build -f apps/api/Dockerfile -t nutrivision-api .
#   docker run -p 8000:8000 --env-file apps/api/.env nutrivision-api
#
# Untuk EC2 tanpa GPU (t3.medium): pakai torch CPU di requirements-api.txt
# Untuk EC2 GPU (g4dn): ganti DEVICE="cuda:0" di apps/api/src/inference.py

FROM python:3.11-slim

WORKDIR /app

# System deps untuk Pillow dan OpenCV headless yang dipakai Ultralytics
RUN apt-get update && apt-get install -y --no-install-recommends \
    libglib2.0-0 \
    libgl1 \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY apps/api/src/requirements-api.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code dan model
COPY apps/api/src/ ./src/
COPY models/production/ ./models/production/

# Working dir = src/ supaya import relatif (inference, nutrition, dll) berjalan
WORKDIR /app/src

EXPOSE 8000

# Jalankan dengan 1 worker untuk MVP (model YOLO tidak thread-safe dengan multi-worker)
# Scale dengan multiple containers (ECS), bukan multiple workers per container
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]
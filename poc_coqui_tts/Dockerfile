FROM python:3.11-slim
WORKDIR /app

# System deps - ADDED espeak-ng
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg libsndfile1 espeak-ng \
    && rm -rf /var/lib/apt/lists/*

# Python deps
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Sidecar application
COPY sidecar.py .
COPY cert.pem key.pem ./

EXPOSE 5002
CMD ["uvicorn", "sidecar:app", "--host", "0.0.0.0", "--port", "5002"]
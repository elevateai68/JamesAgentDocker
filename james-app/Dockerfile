FROM python:3.11-slim
WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends curl && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app.py .
COPY james_personality.txt .
COPY ./static ./static

# Start up with SSL enabled
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]

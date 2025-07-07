#!/bin/bash
cd "$(dirname "$0")"
echo "🔁 Restarting James and Ollama containers..."
docker-compose down
docker-compose build
docker-compose up -d
echo "✅ James system is up."

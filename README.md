# James AI Appliance

An offline-first, privacy-focused conversational AI that runs locally on user hardware without subscriptions. It features a self-contained agent ("James") for basic conversations and tools, with optional "Turbo Mode" for advanced external LLMs.

## Core Philosophy
- Offline-first: No internet required for core functionality.
- Privacy-focused: All processing happens locally.
- Simple UI: Natural language commands in a clean interface.

## Architecture
The system is containerized with Docker and docker-compose, including:
- **james**: FastAPI app for UI and WebSocket handling.
- **ollama-james & ollama-scout**: Local LLMs (qwen2.5:7b) for agent persona and routing.
- **qdrant**: Vector DB for memory/RAG.
- **proxy & coqui-server**: Supporting services for networking and TTS.
- Planned: Self-hosted SearxNG for web search.

Key files:
- `docker-compose.yml`: Service definitions.
- `james-app/app.py`: Main app logic.
- `james-app/langgraph_orchestration.py`: Agent state machine (LangGraph).
- `command_library.yml`: Dynamic commands (planned).

## Setup
1. Clone the repo: `git clone https://github.com/yourusername/JamesAgentDocker.git` (replace URL).
2. Install dependencies: `pip install -r james-app/requirements.txt`.
3. Start: `docker-compose up -d`.
4. Access UI: http://localhost (or configured port).
5. Configure: Set env vars in `.env` (e.g., API keys for Turbo Mode).

## Features
- **Standard Mode**: Local agent with tools (weather, news, crypto prices).
- **Turbo Mode**: External LLMs (e.g., GPT-4o) for advanced tasks.
- **UI Modes**: Chat/Intel views.
- **Dynamic Commands**: Add via YAML (planned).
- **FAQ Access**: Agent references internal knowledge via RAG.

## Challenges & Roadblocks
- Docker misconfigs (e.g., volumes/paths) caused startup issues—fixed by aligning build context.
- Missing packages/logs: Addressed via migrations and requirements.

## Contributing
- Run locally for testing.
- Add features like SearxNG integration.

For questions, contact [your contact info or leave blank for privacy].

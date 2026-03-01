# 🏰 Wololo Coach

> *Real-time, voice-activated strategic advisor for Age of Empires 2 players.*

Ask a question mid-game using Push-to-Talk, get instant spoken coaching advice powered by Gemini 2.5 Flash — grounded in accurate, up-to-date game data.

## Features (MVP)

- 🎙️ **Voice I/O** — Push-to-Talk hotkey, spoken answers via Gemini Live API
- 🧠 **Full Game Knowledge** — All units, civilizations, techs, bonuses, and counters
- ⚡ **Low Latency** — Gemini 2.5 Flash + bidirectional streaming for fast responses
- 🐳 **Dockerized** — Deploy locally or to Google Cloud Run
- 💰 **Cost-Effective** — Scale-to-zero when not playing

## Architecture

```
┌─────────────┐       WebSocket        ┌──────────────────┐
│  PTT Client │◄──────────────────────►│   FastAPI Server  │
│  (Local PC)  │   Audio ↔ Audio       │  (Docker/Cloud)   │
│              │                        │                   │
│  • Hotkeys   │                        │  • Gemini 2.5     │
│  • Mic Input │                        │  • game_data.json │
│  • Speaker   │                        │  • Live API       │
└─────────────┘                        └──────────────────┘
```

## Tech Stack

| Component | Technology |
|-----------|-----------|
| LLM | Gemini 2.5 Flash (Live API) |
| Backend | FastAPI + Uvicorn |
| Client | Python (pynput, sounddevice) |
| Game Data | Extracted from AoE2DE via genieutils-py |
| Deployment | Docker / Google Cloud Run |

## Project Structure

```
aoe2agent/
├── CLAUDE.md              # Project intelligence for AI assistants
├── README.md              # This file
├── pyproject.toml         # Dependencies + config
├── Dockerfile
├── data/
│   ├── extract_game_data.py
│   ├── schemas/
│   │   └── game_data_schema.json
│   └── game_data.json
├── server/
│   ├── main.py            # FastAPI entry point
│   ├── coach.py           # Gemini integration
│   ├── config.py          # Settings
│   └── voice.py           # Live API voice handler
├── client/
│   ├── main.py            # PTT controller
│   ├── hotkeys.py         # Global hotkey listener
│   └── audio.py           # Audio capture + playback
└── tests/
    ├── test_data.py
    ├── test_coach.py
    └── test_api.py
```

## Quick Start

```bash
# Install
pip install -e ".[dev]"

# Extract game data (requires AoE2DE installed)
python data/extract_game_data.py

# Run server
uvicorn server.main:app --reload

# Run client (in another terminal)
python client/main.py
```

## Development Roadmap

- [x] **Phase 0** — Project foundation
- [ ] **Phase 1** — Game data extraction (all units, civs, counters)
- [ ] **Phase 2** — Text chat backend (FastAPI + Gemini)
- [ ] **Phase 3** — Voice client (PTT + Gemini Live API)
- [ ] **Phase 4** — Docker deployment

## License

MIT
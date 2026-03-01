# CLAUDE.md — Wololo Coach Project Intelligence

## Project
**Wololo Coach** — Real-time, voice-activated AoE2 battle coach powered by Gemini 2.5 Flash.

## Architecture
- `/client` — Local Python PTT (Push-to-Talk) client
- `/server` — FastAPI backend (Gemini integration, voice handling)
- `/data` — Game data pipeline: extraction scripts, JSON schemas, output
- `/tests` — All tests (data validation, API, coach Q&A)

## Tech Stack
- **Python 3.12+**
- **Gemini 2.5 Flash** — LLM + Live API for bidirectional voice
- **FastAPI + Uvicorn** — API server
- **genieutils-py** — Extract game data from AoE2DE `.dat` files
- **pynput** — Global hotkeys
- **sounddevice** — Audio capture/playback
- **Docker** — Container deployment

## Status
- [x] **Phase 1: Game Data Extraction** — Units, civs, and counters extracted using `genieutils-py`
- [x] **Phase 2: Text Chat Backend** — FastAPI `/ask` endpoint integrated with Gemini 2.5 Flash
- [x] **Phase 3: Voice Client** — PTT client with audio streaming via Gemini Live API WebSocket proxy
- [ ] **Phase 4: Deployment** — Dockerization and cloud deployment

## Key Decisions
- `data/game_data.json` is the single source of truth for all game knowledge
- Voice I/O uses Gemini Live API (bidirectional WebSocket) — no separate STT/TTS
- Scale-to-zero with `min-instances=1` during active gaming sessions
- No database for MVP — all game data fits in Gemini's 1M token context window
- Game data extracted from local AoE2DE install at `D:\Program Files\Steam\steamapps\common\AoE2DE`

## Game Data Path (WSL)
```
/mnt/d/Program Files/Steam/steamapps/common/AoE2DE
```

## Development Commands
```bash
pip install -e ".[dev]"                    # Install with dev dependencies
uvicorn server.main:app --reload           # Run backend locally
python client/main.py                      # Run PTT client
pytest                                     # Run all tests
pytest tests/test_data.py -v               # Validate game data schema
docker build -t wololo-coach .             # Build container
docker run -p 8000:8000 wololo-coach       # Run container
```

## Coding Conventions
- Type hints on all function signatures
- Docstrings on all public functions/classes
- `config.py` for all environment variables (never hardcode secrets)
- JSON schemas validate all data files
- Tests mirror source structure: `server/coach.py` → `tests/test_coach.py`

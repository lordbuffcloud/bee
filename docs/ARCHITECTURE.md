# Architecture

## Services
- `backend/`: FastAPI runtime, Telegram bot, heartbeat, memory tooling
- `frontend/`: React "Hive Manager"
- `installer/`: Windows-first installation scripts

## Core Loops
- Heartbeat ticks call registered "thumps" for memory updates and upkeep tasks
- Risk monitor observes actions and halts when tolerance is exceeded
- Personality engine evolves via deltas after each tick

## Extensibility
- Tool adapters live in `backend/bee/tools/`
- Memory integrations in `backend/bee/memory/`
- Swarm adapters in `backend/bee/swarm/`

## External References
- EvermemOS: https://github.com/EverMind-AI/EverMemOS/

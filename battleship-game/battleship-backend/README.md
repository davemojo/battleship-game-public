# Battleship Backend

FastAPI backend for the Battleship game with AI opponent and persistent game sessions.

## Repository

https://github.com/davemojo/-battleship-game

## Features

- **RESTful API** for game management and gameplay
- **AI opponent** with intelligent move generation
- **Persistent sessions** using JSON file storage
- **Comprehensive debugging** and error handling
- **CORS enabled** for frontend integration

## API Endpoints

- `POST /game/new` - Create a new game
- `GET /game/{game_id}` - Get game state
- `POST /game/{game_id}/place-ship` - Place a ship
- `POST /game/{game_id}/attack` - Make an attack
- `POST /game/{game_id}/ai-turn` - Trigger AI move

## Development

```bash
poetry install
poetry run fastapi dev app/main.py
```

## Deployment

Deployed on Fly.io: https://app-bqcsmvrs.fly.dev/

## Game Logic

- **Board:** 10x10 grid with ship placement validation
- **Ships:** 5 ships with sizes [5, 4, 3, 3, 2]
- **AI Strategy:** Smart targeting after hits, random fallback
- **Persistence:** Automatic save/load from `data/games/` directory

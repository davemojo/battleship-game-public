# Battleship Game

A full-stack web-based Battleship game where you can play against an AI opponent online.

## Repository

https://github.com/davemojo/-battleship-game

## Features

- **Full-stack web application** with FastAPI backend and React frontend
- **Play against AI** with intelligent move generation
- **Real-time gameplay** with ship placement and turn-based attacks
- **Persistent game sessions** that survive server restarts
- **Responsive design** built with React, TypeScript, and Tailwind CSS
- **Deployed and ready to play** online

## Game URL

🎮 **Play now:** https://battleship-game-45zm432a.devinapps.com/

## Architecture

- **Backend:** FastAPI (Python) with JSON file persistence
- **Frontend:** React + TypeScript + Vite with Tailwind CSS
- **Deployment:** Fly.io backend, Devin Apps frontend
- **Game Logic:** 10x10 grid, 5 ships (Carrier, Battleship, Cruiser, Submarine, Destroyer)

## Development

### Backend
```bash
cd battleship-backend
poetry install
poetry run fastapi dev app/main.py
```

### Frontend
```bash
cd battleship-frontend
npm install
npm run dev
```

## Game Rules

1. Place your 5 ships on your board (Carrier: 5 cells, Battleship: 4 cells, etc.)
2. Take turns attacking the AI's board by clicking on cells
3. Hit all enemy ships to win!
4. AI responds intelligently with strategic targeting

## Technical Details

- **AI Strategy:** Targets adjacent cells after hits, falls back to random attacks
- **Persistence:** Game state saved to disk, survives server auto-suspend
- **Error Handling:** 10-second timeouts, comprehensive debugging, user-friendly messages
- **Debugging:** Production logging active for monitoring and troubleshooting

Built by Devin AI for @davemojo

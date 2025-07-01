from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict, Tuple
import random
import uuid
import json
import os
from pathlib import Path
from enum import Enum

app = FastAPI()

# Disable CORS. Do not remove this for full-stack development.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

class CellState(str, Enum):
    EMPTY = "empty"
    SHIP = "ship"
    HIT = "hit"
    MISS = "miss"

class GameState(str, Enum):
    SETUP = "setup"
    PLAYER_TURN = "player_turn"
    AI_TURN = "ai_turn"
    PLAYER_WON = "player_won"
    AI_WON = "ai_won"

class Ship(BaseModel):
    size: int
    positions: List[Tuple[int, int]]
    hits: int = 0
    
    def is_sunk(self) -> bool:
        return self.hits >= self.size

class Board(BaseModel):
    grid: List[List[CellState]]
    ships: List[Ship]
    
    def __init__(self):
        super().__init__(grid=[[CellState.EMPTY for _ in range(10)] for _ in range(10)], ships=[])

class Game(BaseModel):
    id: str
    player_board: Board
    ai_board: Board
    state: GameState
    current_turn: str  # "player" or "ai"
    
    def __init__(self):
        super().__init__(
            id=str(uuid.uuid4()),
            player_board=Board(),
            ai_board=Board(),
            state=GameState.SETUP,
            current_turn="player"
        )

games: Dict[str, Game] = {}

GAMES_DATA_DIR = Path("data/games")
GAMES_DATA_DIR.mkdir(parents=True, exist_ok=True)

def save_game(game: Game):
    try:
        game_file = GAMES_DATA_DIR / f"{game.id}.json"
        with open(game_file, 'w') as f:
            json.dump(game.model_dump(), f)
    except Exception as e:
        print(f"Error saving game {game.id}: {e}")

def load_game(game_id: str) -> Optional[Game]:
    try:
        game_file = GAMES_DATA_DIR / f"{game_id}.json"
        if game_file.exists():
            with open(game_file, 'r') as f:
                game_data = json.load(f)
                game = Game()
                game.id = game_data['id']
                
                player_board = Board()
                player_board.grid = [[CellState(cell) for cell in row] for row in game_data['player_board']['grid']]
                player_board.ships = [Ship(**ship_data) for ship_data in game_data['player_board']['ships']]
                game.player_board = player_board
                
                ai_board = Board()
                ai_board.grid = [[CellState(cell) for cell in row] for row in game_data['ai_board']['grid']]
                ai_board.ships = [Ship(**ship_data) for ship_data in game_data['ai_board']['ships']]
                game.ai_board = ai_board
                
                game.state = GameState(game_data['state'])
                game.current_turn = game_data['current_turn']
                return game
    except Exception as e:
        print(f"Error loading game {game_id}: {e}")
    return None

def load_all_games():
    try:
        for game_file in GAMES_DATA_DIR.glob("*.json"):
            game_id = game_file.stem
            game = load_game(game_id)
            if game:
                games[game_id] = game
        print(f"Loaded {len(games)} games from disk")
    except Exception as e:
        print(f"Error loading games: {e}")

load_all_games()

class PlaceShipRequest(BaseModel):
    positions: List[Tuple[int, int]]

class AttackRequest(BaseModel):
    x: int
    y: int

def is_valid_ship_placement(board: Board, positions: List[Tuple[int, int]], size: int) -> bool:
    if len(positions) != size:
        return False
    
    for x, y in positions:
        if x < 0 or x >= 10 or y < 0 or y >= 10:
            return False
    
    positions.sort()
    if len(positions) > 1:
        horizontal = all(positions[i][0] == positions[0][0] and positions[i][1] == positions[i-1][1] + 1 
                        for i in range(1, len(positions)))
        vertical = all(positions[i][1] == positions[0][1] and positions[i][0] == positions[i-1][0] + 1 
                      for i in range(1, len(positions)))
        if not (horizontal or vertical):
            return False
    
    for x, y in positions:
        if board.grid[x][y] != CellState.EMPTY:
            return False
    
    return True

def place_ship_on_board(board: Board, positions: List[Tuple[int, int]], size: int):
    ship = Ship(size=size, positions=positions)
    board.ships.append(ship)
    for x, y in positions:
        board.grid[x][y] = CellState.SHIP

def generate_ai_ships(board: Board):
    ship_sizes = [5, 4, 3, 3, 2]
    
    for size in ship_sizes:
        placed = False
        attempts = 0
        while not placed and attempts < 100:
            horizontal = random.choice([True, False])
            
            if horizontal:
                x = random.randint(0, 9)
                y = random.randint(0, 10 - size)
                positions = [(x, y + i) for i in range(size)]
            else:
                x = random.randint(0, 10 - size)
                y = random.randint(0, 9)
                positions = [(x + i, y) for i in range(size)]
            
            if is_valid_ship_placement(board, positions, size):
                place_ship_on_board(board, positions, size)
                placed = True
            
            attempts += 1

def make_ai_move(game: Game) -> Tuple[int, int]:
    print(f"DEBUG: make_ai_move called for game {game.id}")
    board = game.player_board
    
    print(f"DEBUG: Player board state:")
    for i, row in enumerate(board.grid):
        print(f"DEBUG: Row {i}: {[cell.value for cell in row]}")
    
    for x in range(10):
        for y in range(10):
            if board.grid[x][y] == CellState.HIT:
                print(f"DEBUG: Found HIT at ({x}, {y}), looking for adjacent targets")
                for dx, dy in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
                    nx, ny = x + dx, y + dy
                    if 0 <= nx < 10 and 0 <= ny < 10:
                        if board.grid[nx][ny] == CellState.EMPTY or board.grid[nx][ny] == CellState.SHIP:
                            print(f"DEBUG: AI targeting adjacent cell ({nx}, {ny})")
                            return nx, ny
    
    available_cells = []
    for x in range(10):
        for y in range(10):
            if board.grid[x][y] in [CellState.EMPTY, CellState.SHIP]:
                available_cells.append((x, y))
    
    print(f"DEBUG: Available cells for random attack: {len(available_cells)}")
    if available_cells:
        target = random.choice(available_cells)
        print(f"DEBUG: AI choosing random target: {target}")
        return target
    
    print(f"DEBUG: WARNING - No available cells found, using fallback (0, 0)")
    return 0, 0  # Fallback

def process_attack(board: Board, x: int, y: int) -> Dict:
    if board.grid[x][y] == CellState.SHIP:
        board.grid[x][y] = CellState.HIT
        
        for ship in board.ships:
            if (x, y) in ship.positions:
                ship.hits += 1
                sunk = ship.is_sunk()
                return {"hit": True, "sunk": sunk}
        
        return {"hit": True, "sunk": False}
    else:
        board.grid[x][y] = CellState.MISS
        return {"hit": False, "sunk": False}

def check_game_over(board: Board) -> bool:
    return all(ship.is_sunk() for ship in board.ships)

@app.get("/healthz")
async def healthz():
    return {"status": "ok"}

@app.post("/game/new")
async def create_new_game():
    game = Game()
    generate_ai_ships(game.ai_board)
    games[game.id] = game
    save_game(game)
    return {"game_id": game.id, "state": game.state}

@app.get("/game/{game_id}")
async def get_game(game_id: str):
    if game_id not in games:
        game = load_game(game_id)
        if game:
            games[game_id] = game
        else:
            raise HTTPException(status_code=404, detail="Game not found")
    
    game = games[game_id]
    
    ai_grid = []
    for row in game.ai_board.grid:
        ai_row = []
        for cell in row:
            if cell == CellState.SHIP:
                ai_row.append(CellState.EMPTY)  # Hide AI ships
            else:
                ai_row.append(cell)
        ai_grid.append(ai_row)
    
    return {
        "id": game.id,
        "state": game.state,
        "current_turn": game.current_turn,
        "player_board": game.player_board.grid,
        "ai_board": ai_grid,
        "player_ships_remaining": len([s for s in game.player_board.ships if not s.is_sunk()]),
        "ai_ships_remaining": len([s for s in game.ai_board.ships if not s.is_sunk()])
    }

@app.post("/game/{game_id}/place-ship")
async def place_ship(game_id: str, request: PlaceShipRequest):
    if game_id not in games:
        game = load_game(game_id)
        if game:
            games[game_id] = game
        else:
            raise HTTPException(status_code=404, detail="Game not found")
    
    game = games[game_id]
    
    if game.state != GameState.SETUP:
        raise HTTPException(status_code=400, detail="Game is not in setup phase")
    
    ship_sizes = [5, 4, 3, 3, 2]
    current_ships = len(game.player_board.ships)
    
    if current_ships >= len(ship_sizes):
        raise HTTPException(status_code=400, detail="All ships already placed")
    
    expected_size = ship_sizes[current_ships]
    
    if not is_valid_ship_placement(game.player_board, request.positions, expected_size):
        raise HTTPException(status_code=400, detail="Invalid ship placement")
    
    place_ship_on_board(game.player_board, request.positions, expected_size)
    
    if len(game.player_board.ships) == len(ship_sizes):
        game.state = GameState.PLAYER_TURN
        game.current_turn = "player"
    
    save_game(game)
    return {"success": True, "ships_placed": len(game.player_board.ships), "total_ships": len(ship_sizes)}

@app.post("/game/{game_id}/attack")
async def attack(game_id: str, request: AttackRequest):
    if game_id not in games:
        game = load_game(game_id)
        if game:
            games[game_id] = game
        else:
            raise HTTPException(status_code=404, detail="Game not found")
    
    game = games[game_id]
    
    if game.state not in [GameState.PLAYER_TURN, GameState.AI_TURN]:
        raise HTTPException(status_code=400, detail="Game is not in play phase")
    
    if game.current_turn == "player" and game.state == GameState.PLAYER_TURN:
        if game.ai_board.grid[request.x][request.y] in [CellState.HIT, CellState.MISS]:
            raise HTTPException(status_code=400, detail="Cell already attacked")
        
        result = process_attack(game.ai_board, request.x, request.y)
        
        if check_game_over(game.ai_board):
            game.state = GameState.PLAYER_WON
        else:
            game.state = GameState.AI_TURN
            game.current_turn = "ai"
        
        save_game(game)
        return {"result": result, "game_state": game.state}
    
    else:
        raise HTTPException(status_code=400, detail="Not player's turn")

@app.post("/game/{game_id}/ai-turn")
async def ai_turn(game_id: str):
    print(f"DEBUG: ai_turn endpoint called for game {game_id}")
    
    try:
        if game_id not in games:
            print(f"DEBUG: Game {game_id} not in memory, trying to load from disk")
            game = load_game(game_id)
            if game:
                games[game_id] = game
                print(f"DEBUG: Successfully loaded game {game_id} from disk")
            else:
                print(f"DEBUG: Game {game_id} not found on disk either")
                raise HTTPException(status_code=404, detail="Game session not found. Please start a new game.")
        
        game = games[game_id]
        print(f"DEBUG: Game state: {game.state}, current_turn: {game.current_turn}")
        
        if game.state != GameState.AI_TURN or game.current_turn != "ai":
            print(f"DEBUG: Invalid state for AI turn - state: {game.state}, turn: {game.current_turn}")
            raise HTTPException(status_code=400, detail=f"It's not the AI's turn. Current game state: {game.state}")
        
        print(f"DEBUG: Calling make_ai_move")
        x, y = make_ai_move(game)
        print(f"DEBUG: AI chose move ({x}, {y})")
        
        if not (0 <= x < 10 and 0 <= y < 10):
            print(f"DEBUG: ERROR - Invalid AI move coordinates: ({x}, {y})")
            raise HTTPException(status_code=500, detail="AI generated invalid move coordinates. Please try again.")
        
        if game.player_board.grid[x][y] in [CellState.HIT, CellState.MISS]:
            print(f"DEBUG: ERROR - AI trying to attack already attacked cell: ({x}, {y})")
            raise HTTPException(status_code=500, detail="AI attempted to attack the same cell twice. Please try again.")
        
        print(f"DEBUG: Processing attack on player board at ({x}, {y})")
        result = process_attack(game.player_board, x, y)
        print(f"DEBUG: Attack result: {result}")
        
        if check_game_over(game.player_board):
            print(f"DEBUG: Game over - AI won")
            game.state = GameState.AI_WON
        else:
            print(f"DEBUG: Game continues - switching to player turn")
            game.state = GameState.PLAYER_TURN
            game.current_turn = "player"
        
        print(f"DEBUG: Saving game state")
        save_game(game)
        
        response = {
            "ai_move": {"x": x, "y": y},
            "result": result,
            "game_state": game.state
        }
        print(f"DEBUG: Returning response: {response}")
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"DEBUG: Unexpected exception in ai_turn: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"AI turn failed due to an unexpected error: {str(e)}. Please try refreshing the page or starting a new game.")

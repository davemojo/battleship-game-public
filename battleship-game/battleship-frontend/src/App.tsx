import { useState } from 'react'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Anchor, Target, Waves, Trophy, AlertCircle } from 'lucide-react'

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

type CellState = 'empty' | 'ship' | 'hit' | 'miss'
type GameState = 'setup' | 'player_turn' | 'ai_turn' | 'player_won' | 'ai_won'

interface GameData {
  id: string
  state: GameState
  current_turn: string
  player_board: CellState[][]
  ai_board: CellState[][]
  player_ships_remaining: number
  ai_ships_remaining: number
}


const SHIP_SIZES = [5, 4, 3, 3, 2]
const SHIP_NAMES = ['Carrier', 'Battleship', 'Cruiser', 'Submarine', 'Destroyer']

function App() {
  const [gameData, setGameData] = useState<GameData | null>(null)
  const [gameId, setGameId] = useState<string>('')
  const [isPlacingShip, setIsPlacingShip] = useState(false)
  const [selectedCells, setSelectedCells] = useState<[number, number][]>([])
  const [currentShipIndex, setCurrentShipIndex] = useState(0)
  const [message, setMessage] = useState('')
  const [isLoading, setIsLoading] = useState(false)

  const createNewGame = async () => {
    setIsLoading(true)
    try {
      const response = await fetch(`${API_BASE_URL}/game/new`, {
        method: 'POST',
      })
      const data = await response.json()
      setGameId(data.game_id)
      setCurrentShipIndex(0)
      setSelectedCells([])
      setIsPlacingShip(true)
      setMessage(`Place your ${SHIP_NAMES[0]} (${SHIP_SIZES[0]} cells)`)
      await fetchGameData(data.game_id)
    } catch (error) {
      setMessage('Failed to create game. Please try again.')
    }
    setIsLoading(false)
  }

  const fetchGameData = async (id: string) => {
    try {
      const response = await fetch(`${API_BASE_URL}/game/${id}`)
      const data = await response.json()
      setGameData(data)
    } catch (error) {
      setMessage('Failed to fetch game data.')
    }
  }

  const handleCellClick = async (row: number, col: number, isPlayerBoard: boolean) => {
    if (!gameData) return

    if (gameData.state === 'setup' && isPlayerBoard && isPlacingShip) {
      const cellIndex = selectedCells.findIndex(([r, c]) => r === row && c === col)
      
      if (cellIndex >= 0) {
        setSelectedCells(selectedCells.filter((_, i) => i !== cellIndex))
      } else {
        if (selectedCells.length < SHIP_SIZES[currentShipIndex]) {
          setSelectedCells([...selectedCells, [row, col]])
        }
      }
    } else if (gameData.state === 'player_turn' && !isPlayerBoard) {
      if (gameData.ai_board[row][col] === 'hit' || gameData.ai_board[row][col] === 'miss') {
        setMessage('You already attacked this cell!')
        return
      }

      setIsLoading(true)
      try {
        const response = await fetch(`${API_BASE_URL}/game/${gameId}/attack`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ x: row, y: col })
        })
        const data = await response.json()
        
        if (data.result.hit) {
          setMessage(data.result.sunk ? 'Hit and sunk!' : 'Hit!')
        } else {
          setMessage('Miss!')
        }

        if (data.game_state === 'ai_turn') {
          console.log('DEBUG: Triggering AI turn after player attack')
          setTimeout(() => {
            console.log('DEBUG: AI turn timeout executed, calling handleAITurn')
            handleAITurnWithId(gameId)
          }, 1000)
        }

        await fetchGameData(gameId)
      } catch (error) {
        setMessage('Attack failed. Please try again.')
      }
      setIsLoading(false)
    }
  }

  const placeShip = async () => {
    if (selectedCells.length !== SHIP_SIZES[currentShipIndex]) {
      setMessage(`Please select exactly ${SHIP_SIZES[currentShipIndex]} cells for the ${SHIP_NAMES[currentShipIndex]}`)
      return
    }

    setIsLoading(true)
    try {
      const response = await fetch(`${API_BASE_URL}/game/${gameId}/place-ship`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ positions: selectedCells })
      })
      
      if (response.ok) {
        const data = await response.json()
        setSelectedCells([])
        
        if (data.ships_placed < data.total_ships) {
          setCurrentShipIndex(currentShipIndex + 1)
          setMessage(`Place your ${SHIP_NAMES[currentShipIndex + 1]} (${SHIP_SIZES[currentShipIndex + 1]} cells)`)
        } else {
          setIsPlacingShip(false)
          setMessage('All ships placed! Click on the AI board to attack!')
        }
        
        await fetchGameData(gameId)
      } else {
        const error = await response.json()
        setMessage(error.detail || 'Invalid ship placement')
      }
    } catch (error) {
      setMessage('Failed to place ship. Please try again.')
    }
    setIsLoading(false)
  }

  const handleAITurnWithId = async (currentGameId: string) => {
    console.log('DEBUG: handleAITurnWithId called with gameId:', currentGameId)
    
    if (!currentGameId) {
      console.log('DEBUG: AI turn skipped - missing gameId parameter')
      return
    }

    console.log('DEBUG: Starting AI turn request (using passed gameId, bypassing state dependency)')
    setIsLoading(true)
    try {
      const controller = new AbortController()
      const timeoutId = setTimeout(() => {
        console.log('DEBUG: AI turn timeout triggered after 10 seconds')
        controller.abort()
      }, 10000)
      
      console.log('DEBUG: Making AI turn API request to:', `${API_BASE_URL}/game/${currentGameId}/ai-turn`)
      const response = await fetch(`${API_BASE_URL}/game/${currentGameId}/ai-turn`, {
        method: 'POST',
        signal: controller.signal
      })
      
      clearTimeout(timeoutId)
      console.log('DEBUG: AI turn API response status:', response.status)
      
      if (!response.ok) {
        const errorData = await response.json()
        console.log('DEBUG: AI turn API error:', errorData)
        throw new Error(errorData.detail || `AI turn failed with status ${response.status}`)
      }

      const data = await response.json()
      console.log('DEBUG: AI turn API response data:', data)
      
      if (data.result.hit) {
        setMessage(`AI hit your ship at (${data.ai_move.x}, ${data.ai_move.y})${data.result.sunk ? ' and sunk it!' : '!'}`)
      } else {
        setMessage(`AI missed at (${data.ai_move.x}, ${data.ai_move.y})`)
      }

      await fetchGameData(currentGameId)
    } catch (error) {
      console.error('AI turn error:', error)
      if (error instanceof Error && error.name === 'AbortError') {
        setMessage('AI turn timed out after 10 seconds. Please try refreshing the page or starting a new game.')
      } else {
        const errorMessage = error instanceof Error ? error.message : 'Unknown error occurred'
        setMessage(`AI turn failed: ${errorMessage}. Please try refreshing the page.`)
      }
    }
    setIsLoading(false)
  }

  const getCellContent = (cell: CellState, isPlayerBoard: boolean, row: number, col: number) => {
    const isSelected = selectedCells.some(([r, c]) => r === row && c === col)
    
    if (isSelected && isPlayerBoard) {
      return <Anchor className="w-4 h-4 text-blue-600" />
    }
    
    switch (cell) {
      case 'ship':
        return isPlayerBoard ? <Anchor className="w-4 h-4 text-gray-600" /> : null
      case 'hit':
        return <Target className="w-4 h-4 text-red-600" />
      case 'miss':
        return <Waves className="w-4 h-4 text-blue-400" />
      default:
        return null
    }
  }

  const getCellClassName = (cell: CellState, isPlayerBoard: boolean, row: number, col: number) => {
    const isSelected = selectedCells.some(([r, c]) => r === row && c === col)
    const baseClasses = "w-8 h-8 border border-gray-300 flex items-center justify-center cursor-pointer transition-colors"
    
    if (isSelected && isPlayerBoard) {
      return `${baseClasses} bg-blue-200 hover:bg-blue-300`
    }
    
    switch (cell) {
      case 'ship':
        return `${baseClasses} ${isPlayerBoard ? 'bg-gray-200' : 'bg-blue-50 hover:bg-blue-100'}`
      case 'hit':
        return `${baseClasses} bg-red-200`
      case 'miss':
        return `${baseClasses} bg-blue-100`
      default:
        return `${baseClasses} bg-blue-50 hover:bg-blue-100`
    }
  }

  const renderBoard = (board: CellState[][], isPlayerBoard: boolean, title: string) => (
    <Card className="w-full max-w-md">
      <CardHeader>
        <CardTitle className="text-center">{title}</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="grid grid-cols-10 gap-1 mb-4">
          {board.map((row, rowIndex) =>
            row.map((cell, colIndex) => (
              <div
                key={`${rowIndex}-${colIndex}`}
                className={getCellClassName(cell, isPlayerBoard, rowIndex, colIndex)}
                onClick={() => handleCellClick(rowIndex, colIndex, isPlayerBoard)}
              >
                {getCellContent(cell, isPlayerBoard, rowIndex, colIndex)}
              </div>
            ))
          )}
        </div>
        {isPlayerBoard && (
          <div className="text-center">
            <Badge variant="outline">
              Ships: {gameData?.player_ships_remaining || 0}
            </Badge>
          </div>
        )}
        {!isPlayerBoard && (
          <div className="text-center">
            <Badge variant="outline">
              Enemy Ships: {gameData?.ai_ships_remaining || 0}
            </Badge>
          </div>
        )}
      </CardContent>
    </Card>
  )

  const getGameStatusMessage = () => {
    if (!gameData) return ''
    
    switch (gameData.state) {
      case 'setup':
        return 'Place your ships'
      case 'player_turn':
        return 'Your turn - Click on enemy board to attack!'
      case 'ai_turn':
        return 'AI is thinking...'
      case 'player_won':
        return '🎉 You won!'
      case 'ai_won':
        return '💀 AI won!'
      default:
        return ''
    }
  }

  return (
    <div className="min-h-screen bg-gradient-to-b from-blue-50 to-blue-100 p-4">
      <div className="max-w-6xl mx-auto">
        <div className="text-center mb-8">
          <h1 className="text-4xl font-bold text-blue-900 mb-2 flex items-center justify-center gap-2">
            <Anchor className="w-8 h-8" />
            Battleship
          </h1>
          <p className="text-blue-700">Sink all enemy ships to win!</p>
        </div>

        {!gameData ? (
          <div className="text-center">
            <Button 
              onClick={createNewGame} 
              disabled={isLoading}
              size="lg"
              className="bg-blue-600 hover:bg-blue-700"
            >
              {isLoading ? 'Creating Game...' : 'Start New Game'}
            </Button>
          </div>
        ) : (
          <>
            <div className="text-center mb-6">
              <div className="flex items-center justify-center gap-2 mb-2">
                {gameData.state === 'player_won' && <Trophy className="w-6 h-6 text-yellow-500" />}
                {gameData.state === 'ai_won' && <AlertCircle className="w-6 h-6 text-red-500" />}
                <h2 className="text-2xl font-semibold text-blue-900">
                  {getGameStatusMessage()}
                </h2>
              </div>
              {message && (
                <p className="text-lg text-blue-700 mb-2">{message}</p>
              )}
              {isLoading && (
                <p className="text-sm text-blue-600">Processing...</p>
              )}
            </div>

            <div className="flex flex-col lg:flex-row gap-8 justify-center items-start">
              {renderBoard(gameData.player_board, true, "Your Fleet")}
              {renderBoard(gameData.ai_board, false, "Enemy Waters")}
            </div>

            <div className="text-center mt-6">
              {isPlacingShip && selectedCells.length === SHIP_SIZES[currentShipIndex] && (
                <Button 
                  onClick={placeShip}
                  disabled={isLoading}
                  className="bg-green-600 hover:bg-green-700 mr-4"
                >
                  Place {SHIP_NAMES[currentShipIndex]}
                </Button>
              )}
              
              {(gameData.state === 'player_won' || gameData.state === 'ai_won') && (
                <Button 
                  onClick={createNewGame}
                  disabled={isLoading}
                  className="bg-blue-600 hover:bg-blue-700"
                >
                  Play Again
                </Button>
              )}
            </div>
          </>
        )}
      </div>
    </div>
  )
}

export default App

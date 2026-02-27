# SARG Game Engine

Complete implementation of the SARG (Stochastic Adversarial Reasoning Game) engine with full validation, replay capability, and binary storage.

## Components

### 1. Core Engine (`src/engine/`)

#### `enums.py`
- `Player`: Player identifiers (A, B)
- `Action`: Move actions (CHOOSE_DIE_1, CHOOSE_DIE_2, SKIP)
- `SquareType`: Board square types
- Game constants

#### `board.py`
- **Source of truth for board configuration**
- Canonical Board v1.0 with:
  - 5 Safe Zones: {0, 18, 41, 63, 86}
  - 7 Ladders
  - 8 Snakes
  - 6 Scorpions
  - 4 Grapes
- Full validation of mutual exclusivity
- Efficient lookup tables

#### `game_state.py`
- Immutable game state representation
- Complete state validation
- Position, stun, and immunity tracking
- Terminal state detection

#### `game_engine.py`
- Complete FSM implementation
- Full move validation
- Square effect resolution:
  - Ladders (upward promotion)
  - Snakes (downward demotion, blocked by immunity)
  - Scorpions (3-turn stun, blocked by immunity)
  - Grapes (3-turn immunity)
- Capture logic with safe zone protection
- Deterministic state transitions

#### `replay.py`
- Complete game history tracking
- Move-by-move reconstruction
- Pretty printing and visualization
- Game statistics

### 2. Binary Storage (`src/storage/`)

Implements SARG Binary Game Format v1.0 per specification:

#### `game_storage.py`
- File Header (16 bytes)
- Game Header (16 bytes)
- Move encoding (2 bytes per move)
- Efficient storage: ~136 bytes per game

#### `game_writer.py`
- High-level game writing
- Batch operations

#### `game_reader.py`
- Game reconstruction from binary
- Deterministic replay validation
- File validation

## Usage Examples

### Basic Game Simulation

```python
from src.engine import GameEngine, GameState, Action

# Initialize
engine = GameEngine()
state = GameState.initial_state()

# Execute move
dice1, dice2 = 3, 5
action = Action.CHOOSE_DIE_1
new_state, move_info = engine.execute_move(state, dice1, dice2, action)

print(move_info)  # Detailed move information
new_state.pretty_print()  # Visual state display
```

### Complete Game with Replay

```python
from src.engine import GameEngine, GameReplay, simulate_game, Action

# Prepare sequences
dice_sequence = [(3,5), (2,4), (6,1), ...]
action_sequence = [Action.CHOOSE_DIE_1, Action.CHOOSE_DIE_2, ...]

# Simulate
engine = GameEngine()
replay = simulate_game(engine, dice_sequence, action_sequence, verbose=True)

# Analyze
replay.print_summary()
replay.print_full_replay()
stats = replay.get_statistics()
```

### Binary Storage

```python
from pathlib import Path
from src.storage import GameWriter, GameReader
from src.engine import GameEngine

# Write game
writer = GameWriter(Path('data/games/my_games.sarg'))
offset = writer.write_game(replay)

# Read game
reader = GameReader(Path('data/games/my_games.sarg'))
loaded_replay = reader.read_game(offset)

# Validate file
validation_stats = reader.validate_file()
```

### Board Information

```python
from src.engine import CANONICAL_BOARD

CANONICAL_BOARD.print_board_info()

# Query board
is_safe = CANONICAL_BOARD.is_safe_zone(18)  # True
ladder_top = CANONICAL_BOARD.get_ladder_top(4)  # 14
snake_tail = CANONICAL_BOARD.get_snake_tail(97)  # 72
```

## Running Tests

```bash
# Run all tests
pytest tests/ -v

# Run specific test class
pytest tests/test_engine.py::TestBoard -v

# Run with coverage
pytest tests/ --cov=src --cov-report=html
```

## Demo

```bash
# Run demonstration
python demo.py
```

## Key Features

✅ **Full Validation**: Every move validated, LLM-safe  
✅ **Immutable States**: Clean functional state transitions  
✅ **Deterministic**: Exact game reproduction  
✅ **Replay Capability**: Step-by-step game reconstruction  
✅ **Pretty Printing**: Human-readable game visualization  
✅ **Binary Storage**: Efficient 100M+ game storage  
✅ **Comprehensive Tests**: Edge cases covered  
✅ **Type Hints**: Full type annotations  
✅ **Documentation**: Extensive docstrings  

## File Structure

```
src/
├── engine/
│   ├── __init__.py
│   ├── enums.py           # Enums and constants
│   ├── board.py           # Board configuration (SOURCE OF TRUTH)
│   ├── game_state.py      # Immutable game state
│   ├── game_engine.py     # FSM implementation
│   └── replay.py          # Replay and visualization
└── storage/
    ├── __init__.py
    ├── game_storage.py    # Binary format implementation
    ├── game_writer.py     # High-level writer
    └── game_reader.py     # High-level reader
```

## Performance

- State space: 5,222,912 states
- Move execution: < 1ms per move
- Storage: ~136 bytes per game (60 moves avg)
- 100M games: ~13.6 GB storage

## Next Steps

1. Implement 15 heuristic agents (`src/agents/`)
2. Build evaluation system with margin-scaled Elo (`src/evaluation/`)
3. Implement RL training pipeline (`src/rl/`)
4. Add LLM agent interface
5. Create tournament runner for 100M+ game simulations

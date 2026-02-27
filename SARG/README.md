# SARG - Stochastic Adversarial Reasoning Game

Research project implementing a competitive two-player board game with strategic adversarial mechanics for testing heuristic algorithms, RL agents, and LLM-based reasoning systems.

## Project Structure

```
SARG/
├── src/
│   ├── engine/          # Core game engine and state machine
│   ├── agents/          # Heuristic agents (15 variants)
│   ├── storage/         # Binary game storage format
│   ├── rl/              # PPO-based RL agent training
│   └── evaluation/      # Margin-scaled Elo rating system
├── tests/               # Test suite
├── data/
│   ├── games/           # Stored game files
│   ├── logs/            # Training logs
│   └── models/          # Trained model checkpoints
├── configs/             # Configuration files
├── notebooks/           # Jupyter notebooks for analysis
└── docs/                # Game specifications (from GamePlan/)
```

## Quick Start

### Option A: Use Pre-built Image (Recommended for Teammates)

If the image is available on Docker Hub:

```bash
# Pull the pre-built image (saves hours of build time!)
docker compose pull

# Start development container
docker compose up -d sarg-dev
docker exec -it sarg-research bash
```

### Option B: Build from Scratch

### 1. Build Docker Environment

```bash
docker-compose build
```

### 2. Start Development Container

```bash
docker-compose up -d sarg-dev
docker exec -it sarg-research bash
```

### 3. Optional Services

Start Jupyter Notebook:
```bash
docker-compose --profile jupyter up -d jupyter
# Access at http://localhost:8888
```

Start TensorBoard:
```bash
docker-compose --profile tensorboard up -d tensorboard
# Access at http://localhost:6006
```

## Game Specifications

See `docs/` directory for complete specifications:
- Game rules and FSM
- Board definition
- Agent specifications
- Evaluation mechanisms
- RL training protocol
- Binary storage format

## Development

Run tests:
```bash
pytest tests/
```

Format code:
```bash
black src/ tests/
```

Type checking:
```bash
mypy src/
```

## License

Research project - See documentation for details.

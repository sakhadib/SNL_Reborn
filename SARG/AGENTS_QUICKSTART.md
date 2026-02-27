# Agent System - Quick Start

## What's Been Built

✅ **15 Heuristic Agents** - All rule-based strategies from the specification
✅ **Game Manager CLI** - Play games between any two agents
✅ **Comprehensive Testing** - All agents verified working

## Quick Usage

### Run a game
```bash
python3 gamemanager.py --p1 maxim --p2 minim
```

### See turn-by-turn details
```bash
python3 gamemanager.py --p1 hunter --p2 anti_capture --verbose
```

### Available agents
`maxim`, `minim`, `exactor`, `snake_avoider`, `scorpion_avoider`, `safe_preferrer`, `hunter`, `safe_hunter`, `anti_capture`, `grape_seeker`, `immune_aggressor`, `stun_exploiter`, `balanced_eval`, `risk_seeker`, `risk_averse`

## Files Created

- `src/agents/base_agent.py` - Base agent class and helper functions
- `src/agents/heuristic_agents.py` - All 15 agent implementations  
- `src/agents/__init__.py` - Agent registry for CLI
- `gamemanager.py` - Main CLI for playing games
- `test_agents.py` - Verification script
- `AGENTS_README.md` - Comprehensive documentation

## Example Output

```
============================================================
SARG GAME - MAXIM vs MINIM
============================================================
Random seed: 42

============================================================
GAME OVER
============================================================

🏆 WINNER: MAXIM (Player A)

Game Statistics:
  Total turns: 71

Final Positions:
  MAXIM: 100/100
  MINIM: 72/100
```

## Next Steps

These agents are ready to use for:
1. RL training as opponents
2. Baseline evaluation benchmarks
3. Tournament simulations
4. Testing game engine behavior

See `AGENTS_README.md` for detailed documentation of each agent's strategy.

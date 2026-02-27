# SARG Heuristic Agents

This document describes the 15 heuristic agents implemented for SARG and how to use the game manager CLI to play games between them.

## Overview

All agents follow deterministic rule-based strategies derived from the SARG game specification. Each agent implements a different strategy for choosing between two dice in any given turn.

## Agent Descriptions

### 1. **MAXIM** (Pure Forward Greed)
- **Strategy**: Always chooses the larger die
- **Philosophy**: Maximize progress toward goal 100
- **Use case**: Baseline aggressive strategy

### 2. **MINIM** (Minimal Forward Exposure)
- **Strategy**: Always chooses the smaller die
- **Philosophy**: Minimize risk by taking smaller steps
- **Use case**: Baseline conservative strategy

### 3. **EXACTOR** (Endgame Precision)
- **Strategy**: Prioritizes exact win (landing on 100), otherwise uses MAXIM
- **Philosophy**: Avoid overshooting the winning position
- **Use case**: Late-game optimization

### 4. **SNAKE_AVOIDER** (Avoid Demotion)
- **Strategy**: Avoids snake heads; if no safe move, chooses smaller die
- **Philosophy**: Avoid major setbacks from snakes
- **Use case**: Risk mitigation focused on snakes

### 5. **SCORPION_AVOIDER** (Avoid Tempo Loss)
- **Strategy**: Avoids scorpion squares; if no safe move, chooses smaller die
- **Philosophy**: Avoid losing turns to stun
- **Use case**: Tempo preservation

### 6. **SAFE_PREFERRER** (Anchor on Safe Zones)
- **Strategy**: Prioritizes landing on safe zones, otherwise avoids snakes
- **Philosophy**: Secure positions from capture
- **Use case**: Defensive positioning

### 7. **HUNTER** (Aggressive Capture)
- **Strategy**: Always prioritizes capturing opponent, otherwise uses MAXIM
- **Philosophy**: Attack opponent aggressively
- **Use case**: Aggressive adversarial play

### 8. **SAFE_HUNTER** (Smart Capture)
- **Strategy**: Only captures if opponent is far from safe zones (>5 squares), otherwise avoids snakes
- **Philosophy**: Capture only when it has lasting impact
- **Use case**: Strategic adversarial play

### 9. **ANTI_CAPTURE** (Avoid Exposure)
- **Strategy**: Chooses moves where opponent cannot capture next turn
- **Philosophy**: One-step opponent modeling
- **Use case**: Defensive adversarial play

### 10. **GRAPE_SEEKER** (Prioritize Immunity)
- **Strategy**: Seeks grapes for immunity, otherwise avoids snakes
- **Philosophy**: Gain immunity to enable aggressive play
- **Use case**: Immunity exploitation

### 11. **IMMUNE_AGGRESSOR** (Use Immunity Window)
- **Strategy**: When immune, uses MAXIM; otherwise uses SNAKE_AVOIDER
- **Philosophy**: Risk-on when protected, risk-off otherwise
- **Use case**: Context-aware aggression

### 12. **STUN_EXPLOITER** (Exploit Tempo Advantage)
- **Strategy**: When opponent stunned, uses MAXIM; otherwise uses SCORPION_AVOIDER
- **Philosophy**: Capitalize on opponent's weakness
- **Use case**: Opportunistic aggression

### 13. **BALANCED_EVAL** (Weighted Evaluation Function)
- **Strategy**: Evaluates moves with balanced weights:
  - Progress: +1.0
  - Ladder gain: +2.0
  - Snake loss: -2.5
  - Scorpion penalty: -1.5
  - Grape bonus: +1.5
  - Capture bonus: +2.0
  - Exposure penalty: -1.5
- **Philosophy**: Generalist strategy balancing all factors
- **Use case**: Well-rounded gameplay

### 14. **RISK_SEEKER** (Volatility Maximizer)
- **Strategy**: Aggressive high-swing evaluation:
  - Progress: +1.2
  - Ladder gain: +3.0
  - Snake loss: -1.0
  - Scorpion penalty: -0.5
  - Grape bonus: +0.5
  - Capture bonus: +3.0
  - Exposure penalty: -0.5
- **Philosophy**: High risk, high reward
- **Use case**: Aggressive variance-seeking

### 15. **RISK_AVERSE** (Minimize Punishment)
- **Strategy**: Defensive planning with heavy penalties:
  - Progress: +0.8
  - Ladder gain: +1.5
  - Snake loss: -3.5
  - Scorpion penalty: -2.5
  - Grape bonus: +2.0
  - Capture bonus: +1.0
  - Exposure penalty: -2.5
- **Philosophy**: Safety first, avoid setbacks
- **Use case**: Conservative risk mitigation

## Game Manager CLI

### Basic Usage

```bash
python3 gamemanager.py --p1 <agent1> --p2 <agent2>
```

### Options

- `--p1 <agent>`: Choose Player A's agent (required)
- `--p2 <agent>`: Choose Player B's agent (required)
- `--verbose` or `-v`: Show turn-by-turn gameplay details
- `--seed <int>`: Set random seed for reproducibility

### Available Agents

Use these names for `--p1` and `--p2`:
- `maxim`
- `minim`
- `exactor`
- `snake_avoider`
- `scorpion_avoider`
- `safe_preferrer`
- `hunter`
- `safe_hunter`
- `anti_capture`
- `grape_seeker`
- `immune_aggressor`
- `stun_exploiter`
- `balanced_eval`
- `risk_seeker`
- `risk_averse`

## Example Commands

### Quick game (summary only)
```bash
python3 gamemanager.py --p1 maxim --p2 minim
```

### Verbose game (turn-by-turn)
```bash
python3 gamemanager.py --p1 hunter --p2 anti_capture --verbose
```

### Reproducible game with seed
```bash
python3 gamemanager.py --p1 balanced_eval --p2 risk_averse --seed 42
```

### Testing strategic matchups
```bash
# Aggressive vs Defensive
python3 gamemanager.py --p1 hunter --p2 safe_preferrer --verbose

# Risk-seeking vs Risk-averse
python3 gamemanager.py --p1 risk_seeker --p2 risk_averse

# Context-aware agents
python3 gamemanager.py --p1 immune_aggressor --p2 stun_exploiter
```

## Output Format

### Non-verbose mode
Shows only:
- Game header with agent names
- Final winner announcement
- Game statistics (total turns)
- Final positions of both players

### Verbose mode
Shows additionally:
- Turn number
- Both players' positions and status (Normal/Stunned/Immune) at turn start
- Dice rolled each turn
- Action chosen (which die or skip)

## Implementation Details

### Helper Functions
All agents use the `AgentHelper` class which provides:
- `legal(die)`: Check if move is legal
- `landing(die)`: Get landing position (before effects)
- `final_pos(die)`: Get final position (after ladder/snake)
- `is_snake(die)`, `is_scorpion(die)`, `is_grape(die)`, `is_safe(die)`: Query square types
- `captures(die)`: Check if move captures opponent
- `opponent_can_capture(pos)`: Check if opponent can capture at position
- `progress(die)`: Calculate forward progress
- `ladder_gain(die)`, `snake_loss(die)`, `scorpion_penalty(die)`, `grape_bonus(die)`: Effect values
- `capture_bonus(die)`, `exposure_penalty(die)`: Adversarial values

### Agent Architecture
All agents inherit from `BaseAgent` and implement:
```python
def choose_action(self, engine, state, player, dice1, dice2) -> Action
```

Returns one of:
- `Action.CHOOSE_DIE_1`: Choose first die
- `Action.CHOOSE_DIE_2`: Choose second die
- `Action.SKIP`: Skip turn (when no legal moves)

## Next Steps

These heuristic agents serve as:
1. **Baselines** for RL agent evaluation
2. **Opponents** for self-play training
3. **Behavior examples** for imitation learning
4. **Test cases** for game engine validation

Future work includes:
- Tournament runner for round-robin evaluation
- Statistical analysis of agent performance
- Margin-scaled Elo rating system
- RL agent training using these baselines

# RL Agent V1 - Technical Specification
## Stochastic Adversarial Reasoning Game (SARG)

**Version:** 1.0  
**Framework:** Stable-Baselines3 (PPO)  
**Last Updated:** 2026-02-28

---

## 1. Overview

This document specifies the complete implementation of the first reinforcement learning agent (RL-V1) for SARG, including:

- Gym environment wrapper for SARG game engine
- PPO architecture and hyperparameters
- 4-phase curriculum training pipeline
- Checkpoint and resume mechanism
- Evaluation protocol against heuristic baselines
- Console monitoring system with real-time metrics

**Design Philosophy:**
- Memory-efficient: No game replay storage, learning happens online
- Progressive: Checkpoints every 10k episodes with auto-resume
- Curriculum-driven: 4 phases from random to self-play
- Evaluation-integrated: Test vs all heuristics every 50k episodes

---

## 2. Environment Specification

### 2.1 Observation Space

**Type:** `Box(6,)` - Continuous vector normalized to [0, 1]

```python
observation = np.array([
    self_position / 100.0,      # [0, 1] - Agent's current position
    self_stun_counter / 3.0,    # [0, 1] - Agent's stun duration (0-3 turns)
    self_immune_counter / 3.0,  # [0, 1] - Agent's immunity duration (0-3 turns)
    opp_position / 100.0,       # [0, 1] - Opponent's position
    opp_stun_counter / 3.0,     # [0, 1] - Opponent's stun duration
    opp_immune_counter / 3.0    # [0, 1] - Opponent's immunity duration
], dtype=np.float32)
```

**Rationale:** 
- Minimal sufficient state representation (6 features)
- Position and status effects fully define strategic context
- Normalized to [0, 1] for stable neural network training
- No dice values in observation (part of action decision, not state)

### 2.2 Action Space

**Type:** `Discrete(3)` - Three possible actions

```python
action_mapping = {
    0: "use_dice_1",  # Move using first dice value
    1: "use_dice_2",  # Move using second dice value
    2: "skip"         # Skip turn (mandatory when stunned or both dice illegal)
}
```

**Action Validity:**
- Actions 0/1 valid only if: not stunned AND dice value legal (pos + dice ≤ 100)
- Action 2 always valid (can choose to skip even if moves available)

### 2.3 Action Masking

Invalid actions are masked to guide policy and prevent illegal moves:

**Masking Rules:**
1. **Agent stunned** (stun_counter > 0): Mask actions 0 and 1 → only skip valid
2. **Dice 1 illegal** (pos + d1 > 100): Mask action 0
3. **Dice 2 illegal** (pos + d2 > 100): Mask action 1
4. **Both dice illegal** AND stunned: Only action 2 (skip) valid

**Implementation:**
Uses `sb3_contrib.common.maskable.policies.MaskableActorCriticPolicy` for efficient action masking during training and inference.

```python
def action_masks(self) -> np.ndarray:
    """Returns binary mask [1, 1, 1] where 1 = valid, 0 = invalid"""
    mask = np.ones(3, dtype=np.int8)
    
    if self.state.stun_counter[self.rl_player] > 0:
        mask[0] = 0  # Cannot use dice 1
        mask[1] = 0  # Cannot use dice 2
        return mask
    
    current_pos = self.state.positions[self.rl_player]
    if current_pos + self.dice1 > 100:
        mask[0] = 0
    if current_pos + self.dice2 > 100:
        mask[1] = 0
    
    return mask
```

### 2.4 Reward Structure

**Margin-Scaled Terminal Rewards:**

Rewards incorporate win/loss outcome AND victory margin to encourage decisive wins:

$$
R_{win} = +100 \times \left(1 + 0.75 \times \frac{100 - L_{final}}{100}\right)
$$

$$
R_{loss} = -100 \times \left(1 + 0.75 \times \frac{100 - L_{final}}{100}\right)
$$

Where $L_{final}$ is the loser's final position (0-100).

**Step Penalty:** -0.1 per turn (encourages efficiency, prevents infinite loops)

**Total Episode Reward Examples:**
- **Crushing win** (opponent at 0): +175 - 0.1×turns
- **Close win** (opponent at 99): +101.25 - 0.1×turns  
- **Close loss** (self at 99): -101.25 - 0.1×turns
- **Crushing loss** (self at 0): -175 - 0.1×turns

**Design Rationale:**
- Margin-scaling aligns with Elo rating system (already used for heuristics)
- Encourages aggressive play and decisive victories
- Step penalty prevents stalling tactics
- Symmetric rewards for win/loss ensure balanced learning

---

## 3. PPO Architecture

### 3.1 Policy Network (Actor)

**Architecture:** Multi-Layer Perceptron (MLP) with 2 hidden layers

```
Input: observation (6,)
  ↓
Dense(256, activation=tanh)
  ↓
Dense(256, activation=tanh)
  ↓
Dense(3, activation=softmax)  [action probabilities]
```

**Key Properties:**
- **Activation:** `tanh` (symmetric, suitable for normalized inputs [-1, 1])
- **Hidden Size:** 256 units (sufficient for 6-input observation space)
- **Depth:** 2 layers (balances expressiveness and training stability)
- **Initialization:** Orthogonal initialization (default in SB3, proven effective for RL)

### 3.2 Value Network (Critic)

**Architecture:** Separate value head (shared backbone optional)

```
Input: observation (6,)
  ↓
Dense(256, activation=tanh)
  ↓
Dense(256, activation=tanh)
  ↓
Dense(1, activation=linear)  [state value estimate]
```

**Purpose:** Estimates expected return from current state for advantage calculation.

### 3.3 Hyperparameters

| Parameter | Value | Rationale |
|-----------|-------|-----------|
| **Learning Rate** | 3e-4 | Standard PPO learning rate, proven stable |
| **Batch Size** | 2048 | Large enough for stable updates, fits in memory |
| **n_steps** | 2048 | Rollout buffer size (episodes collected before update) |
| **n_epochs** | 10 | Optimization epochs per rollout |
| **Gamma (γ)** | 0.99 | Discount factor (values future rewards highly) |
| **GAE Lambda (λ)** | 0.95 | Generalized Advantage Estimation smoothing |
| **Clip Range** | 0.2 | PPO clip parameter (prevents large policy updates) |
| **Value Loss Coef** | 0.5 | Weight for value function loss |
| **Entropy Coef** | 0.01 | Entropy bonus (encourages exploration) |
| **Max Grad Norm** | 0.5 | Gradient clipping (prevents exploding gradients) |
| **Target KL** | None | No early stopping based on KL divergence |

**Action Masking:** Enabled via `MaskablePPO` from `sb3_contrib`

---

## 4. Curriculum Training Pipeline

### 4.1 Four-Phase Curriculum

Training progresses through 4 phases with increasing difficulty:

#### **Phase 1: Random Opponent (Exploration)**
- **Opponent:** Random agent (uniform action selection from valid actions)
- **Episodes:** 500,000 - 1,000,000
- **Goal:** Learn basic game mechanics, valid action selection, board navigation
- **Progression Criterion:** Win rate ≥ 80% over last 10,000 episodes

#### **Phase 2: Weak Heuristics (Fundamentals)**
- **Opponents:** MAXIM, MINIM, EXACTOR (basic position-focused agents)
- **Episodes:** 500,000 - 1,000,000
- **Goal:** Learn strategic positioning, dice selection
- **Progression Criterion:** Combined win rate ≥ 60% vs all 3 agents

#### **Phase 3: Strong Heuristics (Mastery)**
- **Opponents:** All 15 heuristic agents (including evaluation-based agents)
- **Episodes:** 1,000,000 - 2,000,000
- **Goal:** Master complex strategies (risk assessment, trap avoidance, special cells)
- **Progression Criterion:** Combined win rate ≥ 55% vs all 15 agents

#### **Phase 4: Self-Play (Superhuman)**
- **Opponents:** Snapshots of own past versions + best heuristics
- **Episodes:** 2,000,000 - 5,000,000
- **Goal:** Discover novel strategies beyond human-designed heuristics
- **Progression Criterion:** Training completion or manual stop

**Total Training Budget:** 4M - 9M episodes (~10-20 hours on modern CPU)

### 4.2 Automatic Progression

The trainer automatically advances phases based on performance:

```python
# Example progression logic
if current_phase == 1:
    if recent_win_rate >= 0.80:
        advance_to_phase_2()
elif current_phase == 2:
    if avg_win_rate_vs_weak_heuristics >= 0.60:
        advance_to_phase_3()
elif current_phase == 3:
    if avg_win_rate_vs_all_heuristics >= 0.55:
        advance_to_phase_4()
```

**Manual Override:** `--phase N` flag allows resuming at specific phase.

### 4.3 Snapshot Management (Phase 4)

During self-play, agent plays against historical versions of itself:

- **Snapshot Frequency:** Every 100,000 episodes
- **Snapshot Pool:** Last 5 snapshots + current best
- **Opponent Selection:** 
  - 70% from snapshot pool (self-play)
  - 30% from top-5 heuristics (anchoring)

**Purpose:** Prevents strategy collapse, maintains diverse learning signal

---

## 5. Checkpointing & Resume

### 5.1 Checkpoint Structure

Checkpoints saved every 10,000 episodes to `data/rl_checkpoints/`:

```
data/rl_checkpoints/
├── rl_v1_latest.zip          # Most recent model
├── rl_v1_best.zip            # Best model by win rate
├── rl_v1_episode_50000.zip   # Periodic snapshot
├── training_state.json       # Training metadata
└── snapshots/
    ├── snapshot_100k.zip
    ├── snapshot_200k.zip
    └── ...
```

### 5.2 Training State Metadata

`training_state.json` tracks:
```json
{
  "total_episodes": 523000,
  "current_phase": 2,
  "phase_episodes": 23000,
  "best_win_rate": 0.687,
  "recent_win_rate": 0.692,
  "last_checkpoint": "2026-02-28T14:23:45",
  "phase_progression": {
    "phase_1_completed": true,
    "phase_2_completed": false,
    "phase_1_final_wr": 0.847
  }
}
```

### 5.3 Resume Logic

On training restart:
1. Load `training_state.json`
2. Load `rl_v1_latest.zip` model weights
3. Resume from saved episode count and phase
4. Continue curriculum from interrupted point

**No Data Loss:** Even if interrupted mid-episode, resumes from last checkpoint.

---

## 6. Evaluation Protocol

### 6.1 Periodic Evaluation (Every 50k Episodes)

During training, pause and evaluate agent against all 15 heuristics:

**Evaluation Games:**
- 100 games per heuristic opponent
- 1,500 total games per evaluation
- Alternating starting player (50 as Player A, 50 as Player B)
- Fixed seed for reproducibility

**Metrics Collected:**
- Win rate vs each opponent
- Average margin of victory
- Estimated Elo rating (vs heuristic baselines)
- Games per phase progression

### 6.2 Evaluation Output

Results logged to `data/rl_evaluation/`:
```
evaluation_episode_50000.json
evaluation_episode_100000.json
...
```

Each file contains:
```json
{
  "episode": 50000,
  "phase": 1,
  "timestamp": "2026-02-28T12:34:56",
  "results": {
    "maxim": {"wins": 98, "losses": 2, "avg_margin": 87.3},
    "minim": {"wins": 100, "losses": 0, "avg_margin": 95.1},
    ...
  },
  "overall_win_rate": 0.712,
  "estimated_elo": 1647
}
```

### 6.3 Final Evaluation

After training completes, comprehensive evaluation:
- 1,000 games per heuristic (15,000 total)
- Calculate final Elo rating
- Generate head-to-head matrix
- Compare to tournament results

---

## 7. Console Monitoring

### 7.1 Real-Time Display (Rich Library)

During training, live dashboard shows:

```
╭─────────────────────────────────────────────────────────────╮
│              SARG RL-V1 Training Dashboard                  │
├─────────────────────────────────────────────────────────────┤
│ Phase: 2/4 - Weak Heuristics                               │
│ Episode: 523,450 / 9,000,000                               │
│ Progress: ████████████░░░░░░░░░░░░░░░░░░░ 5.8%             │
│                                                             │
│ Current Session:                                            │
│   Episodes this run: 23,450                                │
│   Time elapsed: 2h 34m 12s                                 │
│   Episodes/sec: 2.53                                       │
│   ETA to next eval: 1h 12m                                 │
│                                                             │
│ Performance:                                                │
│   Recent Win Rate: 69.2% (last 5000 games)                │
│   Phase Win Rate: 64.7% (since phase start)               │
│   Best Win Rate: 72.1% (episode 510k)                     │
│   Estimated Elo: ~1580                                     │
│                                                             │
│ Learning Metrics:                                           │
│   Avg Episode Reward: +87.3                                │
│   Policy Entropy: 0.45                                     │
│   Value Loss: 12.34                                        │
│   Policy Loss: 0.0234                                      │
│                                                             │
│ Phase Progress:                                             │
│   Phase 1: ✓ Completed (842k episodes, 84.7% WR)          │
│   Phase 2: ⏳ In Progress (23k / 500k min)                 │
│   Phase 3: ⏸ Locked (need 60% WR in Phase 2)              │
│   Phase 4: ⏸ Locked                                        │
│                                                             │
│ Last Checkpoint: 2026-02-28 14:23:45 (episode 520k)       │
│ Next Checkpoint: episode 530k (in 6,550 episodes)         │
╰─────────────────────────────────────────────────────────────╯

Current Opponent: EXACTOR | Episode Length: 47 turns | Result: WIN (+132.5)
```

### 7.2 Logged Metrics

**TensorBoard Integration:**
- Episode rewards
- Win rates (overall, per-phase, per-opponent)
- Policy/value losses
- Entropy
- Episode lengths
- Estimated Elo progression

**Access:** `tensorboard --logdir data/rl_logs/`

---

## 8. Configuration

### 8.1 Default Configuration (`src/rl/config.py`)

```python
DEFAULT_CONFIG = {
    # Network Architecture
    "policy_type": "MlpPolicy",
    "hidden_size": 256,
    "n_layers": 2,
    "activation": "tanh",
    
    # PPO Hyperparameters
    "learning_rate": 3e-4,
    "n_steps": 2048,
    "batch_size": 2048,
    "n_epochs": 10,
    "gamma": 0.99,
    "gae_lambda": 0.95,
    "clip_range": 0.2,
    "ent_coef": 0.01,
    "vf_coef": 0.5,
    "max_grad_norm": 0.5,
    
    # Training Schedule
    "phase_1_min_episodes": 500000,
    "phase_2_min_episodes": 500000,
    "phase_3_min_episodes": 1000000,
    "phase_4_min_episodes": 2000000,
    
    # Progression Criteria
    "phase_1_target_wr": 0.80,
    "phase_2_target_wr": 0.60,
    "phase_3_target_wr": 0.55,
    
    # Checkpointing
    "checkpoint_freq": 10000,
    "eval_freq": 50000,
    "eval_games_per_opponent": 100,
    
    # Paths
    "checkpoint_dir": "data/rl_checkpoints",
    "eval_dir": "data/rl_evaluation",
    "log_dir": "data/rl_logs",
}
```

### 8.2 CLI Overrides

```bash
# Override learning rate and batch size
python train_rl.py --lr 1e-4 --batch-size 4096

# Start at specific phase
python train_rl.py --phase 3 --resume

# Quick test run
python train_rl.py --episodes 10000 --eval-freq 5000
```

---

## 9. Implementation Files

### 9.1 File Structure

```
src/rl/
├── __init__.py              # Module exports
├── config.py                # Hyperparameters and paths
├── environment.py           # Gym environment wrapper
├── rl_agent.py              # MaskablePPO agent wrapper
├── trainer.py               # 4-phase curriculum trainer
├── evaluator.py             # Evaluation vs heuristics
└── callbacks.py             # Checkpointing, logging, monitoring

train_rl.py                  # CLI entry point
```

### 9.2 Key Classes

- **`SARGEnv(gym.Env)`**: Gym environment implementing SARG game
- **`RLAgent`**: Wrapper for MaskablePPO with save/load
- **`CurriculumTrainer`**: 4-phase training orchestrator
- **`Evaluator`**: Comprehensive evaluation system
- **`CheckpointCallback`**: Auto-save every N episodes
- **`EvaluationCallback`**: Periodic eval every 50k episodes
- **`ConsoleCallback`**: Real-time Rich dashboard updates

---

## 10. Memory & Performance

### 10.1 Memory Efficiency

**Design Decisions:**
- No replay buffer (PPO is on-policy)
- No game history storage (only learning online)
- Checkpoint compression (zip format)
- Periodic cleanup of old snapshots

**Expected Memory Usage:**
- Model parameters: ~2 MB
- Rollout buffer: ~50 MB (2048 steps × 6 obs × 4 bytes)
- Total: <100 MB during training

### 10.2 Training Time Estimates

On modern CPU (e.g., AMD Ryzen 9 / Intel i9):
- **Phase 1:** 2-4 hours (500k-1M episodes vs random)
- **Phase 2:** 2-4 hours (500k-1M episodes vs weak heuristics)
- **Phase 3:** 4-8 hours (1M-2M episodes vs all heuristics)
- **Phase 4:** 8-20 hours (2M-5M episodes self-play)

**Total:** 16-36 hours for full curriculum (conservative estimate)

**GPU Acceleration:** Not required (MLP policy, small network)

---

## 11. Expected Outcomes

### 11.1 Performance Targets

**After Phase 1:** 
- 80%+ win rate vs random agent
- Basic understanding of board mechanics

**After Phase 2:**
- 60%+ win rate vs MAXIM, MINIM, EXACTOR
- Strategic dice selection mastery

**After Phase 3:**
- 55%+ win rate vs all 15 heuristics
- Estimated Elo: 1600-1700 (comparable to top heuristics)

**After Phase 4:**
- 60-70%+ win rate vs all heuristics
- Estimated Elo: 1700-1850+ (superhuman)
- Novel strategies not present in heuristics

### 11.2 Success Metrics

1. **Beats all heuristics consistently** (60%+ win rate)
2. **Elo rating > 1700** (higher than RISK_SEEKER/RISK_AVERSE at ~1810)
3. **Strategic diversity** (uses both dice intelligently, not just max/min)
4. **Robust across opponents** (no single hard counter)

---

## 12. Future Extensions (V2+)

### 12.1 Potential Improvements

- **Larger networks:** 512-unit hidden layers
- **Recurrent policy:** LSTM/GRU for temporal reasoning
- **Advanced curriculum:** Adaptive opponent difficulty
- **Multi-agent training:** Simultaneous co-evolution
- **Transfer learning:** Bootstrap from V1 for faster V2 training

### 12.2 Research Directions

- Analyze learned strategies vs heuristics
- Visualize policy attention on board positions
- Test generalization to modified board configurations
- Compare PPO vs other algorithms (DQN, SAC, A3C)

---

## 13. References

### 13.1 Frameworks & Libraries

- **Stable-Baselines3:** https://stable-baselines3.readthedocs.io/
- **SB3-Contrib:** https://sb3-contrib.readthedocs.io/ (MaskablePPO)
- **Gymnasium:** https://gymnasium.farama.org/
- **Rich:** https://rich.readthedocs.io/

### 13.2 Papers

- Schulman et al. (2017): "Proximal Policy Optimization Algorithms"
- Huang et al. (2020): "The Surprising Effectiveness of PPO in Cooperative Multi-Agent Games"
- OpenAI (2019): "Dota 2 with Large Scale Deep Reinforcement Learning"

---

**Document Version:** 1.0  
**Last Updated:** 2026-02-28  
**Status:** Implementation Ready

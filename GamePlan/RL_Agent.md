# Reinforcement Learning Agent Specification

## Stochastic Adversarial Reasoning Game (SARG)

This document defines the complete RL training pipeline, reward structure, architecture, curriculum, and evaluation protocol. It is sufficient to implement the RL agent without additional design assumptions.

 

# 1. Problem Formulation

The environment is modeled as a finite episodic Markov Decision Process (MDP):

$$
\mathcal{M} = (S, A, P, R, \gamma)
$$

Where:

* $S$ = state space (5,222,912 states)
* $A = \{0,1,2\}$ = actions
* $P(s'|s,a)$ = transition function (includes dice stochasticity)
* $R$ = reward function
* $\gamma$ = discount factor

Episodes terminate when one player reaches cell 100.

 

# 2. Observation Representation

The agent observes the full game state from its own perspective.

State vector:

$$
o = \begin{bmatrix}
\frac{\text{self pos}}{100} \\
\frac{\text{self stun}}{3} \\
\frac{\text{self immune}}{3} \\
\frac{\text{opp pos}}{100} \\
\frac{\text{opp stun}}{3} \\
\frac{\text{opp immune}}{3}
\end{bmatrix}
$$

All values are normalized to $[0,1]$.

Turn indicator is not required because agent only acts on its own turns.

Observation dimension = 6.

 

# 3. Action Space

Discrete(3):

* $0$ $\to$ choose_die_1
* $1$ $\to$ choose_die_2
* $2$ $\to$ skip

Action masking must be applied:

* Mask illegal dice ($\text{pos} + d > 100$)
* Skip always allowed
* If stunned $\to$ only skip allowed

Masked actions receive probability 0 before sampling.

 

# 4. Reward Function

Reward must be stationary, bounded, and dominance-sensitive.

## 4.1 Terminal Reward

Let:

* $S = 1$ if win, $0$ if loss
* $D = 100 -$ losing_position
* $D_{\text{rel}} = D / 100$
* $\alpha = 0.75$

Define margin multiplier:

$$
M = 1 + \alpha D_{\text{rel}}
$$

Terminal reward:

If win:

$$
r = +M
$$

If loss:

$$
r = -M
$$

This yields:

$$
r \in [- (1+\alpha), + (1+\alpha)]
$$

With $\alpha = 0.75$:

$$
r \in [-1.75, +1.75]
$$

 

## 4.2 Intermediate Shaping (Small Magnitude)

To stabilize learning:

* $+0.01 \times$ forward_progress
* $+0.10$ for capture
* $-0.15$ for being captured
* $-0.10$ for scorpion stun
* $+0.08$ for grape pickup

Constraint:

Sum of shaping during full game must be $< 1$ in magnitude, so terminal reward dominates.

 

# 5. Discount Factor

$$
\gamma = 0.99
$$

High discount to preserve long-horizon reasoning.

 

# 6. Algorithm Choice

Algorithm: Proximal Policy Optimization (PPO)

Reasons:

* Stable under stochastic dynamics
* Handles discrete action space
* Compatible with action masking
* Strong empirical reliability

 

# 7. Network Architecture

Input: 6-dimensional vector

Policy Network:

* $\text{Linear}(6 \to 128)$
* ReLU
* $\text{Linear}(128 \to 128)$
* ReLU
* $\text{Linear}(128 \to 64)$
* ReLU
* $\text{Linear}(64 \to 3)$ $\to$ action logits

Value Network:

* Shared backbone or separate
* Final output: scalar value estimate

No recurrent memory required.

 

# 8. Training Pipeline

## Phase 1 — Random Opponent

* Train 500k–1M episodes vs random policy.
* Goal: learn basic movement and exact landing.

## Phase 2 — Weak Heuristics

Train against:

* MAXIM
* MINIM
* SNAKE_AVOIDER

Opponent randomly sampled per episode.

## Phase 3 — Mixed Pool

Opponent sampled from:

* All 15 heuristic agents
* Previous RL snapshot (self-play)

Uniform random selection.

## Phase 4 — Self-Play Fine-Tuning

* 50% games vs latest snapshot
* 50% games vs random heuristic pool

Prevents overfitting.

 

# 9. PPO Hyperparameters

Recommended starting values:

* Learning rate: $3 \times 10^{-4}$
* Batch size: 4096 transitions
* Mini-batch size: 256
* PPO clip: 0.2
* Entropy coefficient: 0.01
* Value loss coefficient: 0.5
* Max gradient norm: 0.5
* Update epochs per batch: 4

 

# 10. Curriculum Strategy

Optional staged complexity:

**Stage 1:**

* Disable scorpions and grapes.

**Stage 2:**

* Enable scorpions.

**Stage 3:**

* Enable grapes.

**Stage 4:**

* Enable capture.

Each stage trained until win rate $> 60\%$ vs baseline before progressing.

 

# 11. Training Stability Controls

* Normalize rewards.
* Use Generalized Advantage Estimation (GAE $\lambda = 0.95$).
* Clip value function updates.
* Early stopping if KL divergence too large.

 

# 12. Convergence Criteria

Training considered stable when:

* Win rate $> 65\%$ vs balanced heuristic pool.
* Margin-Elo rating stabilizes within $\pm 10$ over 200k games.
* Policy entropy converges (no collapse).

 

# 13. Evaluation Protocol

After training:

* Disable exploration (argmax policy).
* Freeze network weights.
* Play 1000 games vs each heuristic.
* Compute margin-scaled Elo.
* Compare against heuristic rankings.

Additionally:

* Measure average win margin.
* Measure capture frequency.
* Measure grape utilization rate.
* Measure snake avoidance rate.

 

# 14. Ablation Experiments

Train three variants:

1. Terminal reward only
2. Terminal + shaping
3. Terminal + margin scaling

Compare convergence speed and final Elo.

 

# 15. Final Output Artifact

The RL agent must export:

* Trained model weights
* Deterministic inference mode
* Version tag
* Training configuration file
* Seed for reproducibility

 

# 16. Expected Emergent Behavior

If training successful, agent should:

* Time grape pickups before large snakes
* Exploit opponent stun windows
* Avoid exposure near non-safe zones
* Execute precise endgame landing
* Use capture strategically

 

This completes the formal RL agent design and training specification.

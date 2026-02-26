# Deterministic Heuristic Agents Specification  
## Stochastic Adversarial Reasoning Game (SARG)

All agents are deterministic and depend only on:

- Current full state
- Dice outcomes ($d_1$, $d_2$)
- Fixed board definition

**Action space per turn:**

$$
A = \{ \text{choose die 1}, \text{choose die 2}, \text{skip} \}
$$

**Helper function definitions:**

Let $d$ denote a die value. Define:

- $\text{legal}(d) := \text{pos} + d \leq 100$
- $\text{landing}(d) := \text{pos} + d$
- $\text{final\_pos}(d) :=$ position after applying square effect (including snake/ladder, ignoring capture)
- $\text{is\_snake}(d) :=$ $\text{landing}(d)$ is snake head and not immune
- $\text{is\_scorpion}(d) :=$ $\text{landing}(d)$ is scorpion and not immune
- $\text{is\_grape}(d) :=$ $\text{landing}(d)$ is grapes
- $\text{is\_safe}(d) := \text{landing}(d) \in \text{SafeZones}$
- $\text{captures}(d) :=$ $\text{final\_pos}(d) = \text{opponent\_pos}$ and opponent not on safe zone

**Illegal move handling:**

- If $\text{legal}(d) = \text{false}$ $\to$ move treated as illegal
- If both moves illegal $\to$ skip

                      --

# I. Primitive Greedy Agents

## 1. MAXIM

Rule:
1. Filter legal dice.
2. Choose die with maximum d.
3. If none legal $\to$ skip.

**Pseudocode:**

```python
if legal(d1) and legal(d2):
    return die with max(d1, d2)
elif legal(d1):
    return d1
elif legal(d2):
    return d2
else:
    return skip
```

 

## 2. MINIM

Rule:
1. Filter legal dice.
2. Choose die with minimum d.
3. If none legal $\to$ skip.

 

## 3. EXACTOR

Rule:
1. If $\text{landing}(d) = 100$ $\to$ choose it.
2. Else behave as MAXIM.

**Pseudocode:**

```python
if legal(d1) and landing(d1) == 100:
    return d1
if legal(d2) and landing(d2) == 100:
    return d2
return MAXIM_policy()
```

                      --

# II. Risk-Aware Agents

## 4. SNAKE_AVOIDER

Rule priority:
1. Prefer legal move not landing on snake.
2. If both non-snake $\to$ choose larger.
3. If both snake $\to$ choose smaller snake.
4. If one illegal and one snake $\to$ skip.

**Pseudocode:**

```python
safe_moves = [d for d in legal_moves if not is_snake(d)]

if safe_moves:
    return max(safe_moves)
else:
    if both_legal:
        return min(d1, d2)
    else:
        return skip
```

 

## 5. SCORPION_AVOIDER

Rule:
1. Avoid scorpion if possible.
2. Among safe moves choose larger.
3. If both scorpion $\to$ choose smaller.

 

## 6. SAFE_PREFERRER

Rule priority:
1. If any legal move lands on safe zone $\to$ choose it.
2. Else avoid snake.
3. Else choose larger legal.
4. Else skip.

                      --

# III. Capture-Oriented Agents

## 7. HUNTER

Rule:
1. If any legal move captures opponent $\to$ choose it.
2. Else MAXIM.

**Pseudocode:**

```python
if legal(d1) and captures(d1):
    return d1
if legal(d2) and captures(d2):
    return d2
return MAXIM_policy()
```

 

## 8. SAFE_HUNTER

Rule:
1. Capture only if opponent not within 5 cells of safe zone.
2. Else avoid snake.
3. Else MAXIM.

 

## 9. ANTI_CAPTURE

**Define exposure:**

$\text{exposed}(d) :=$ opponent can capture new position in one turn

**Rule:**
1. Avoid exposed moves.
2. Among safe moves choose largest.
3. Else choose smallest legal.
4. Else skip.

                      --

# IV. Status-Oriented Agents

## 10. GRAPE_SEEKER

Rule:
1. If legal move lands on grapes $\to$ choose it.
2. Else avoid snake.
3. Else MAXIM.

 

## 11. IMMUNE_AGGRESSOR

**Rule:**

```python
if immunity_counter > 0:
    return MAXIM_policy()
else:
    # Avoid snake, then MAXIM
    return SNAKE_AVOIDER_policy()
```

 

## 12. STUN_EXPLOITER

**Rule:**

```python
if opponent_stun > 0:
    return MAXIM_policy()
else:
    # Avoid scorpion, then MAXIM
    return SCORPION_AVOIDER_policy()
```

                      --

# V. Evaluation-Based Agents

These agents compute a numeric score for each legal move and select the maximum-scoring action.

**General evaluation form:**

For each legal die $d$:

$$
\begin{align*}
\text{score}(d) =\, &+ w_1 \cdot \text{progress}(d) \\
&+ w_2 \cdot \text{ladder\_gain}(d) \\
&- w_3 \cdot \text{snake\_loss}(d) \\
&- w_4 \cdot \text{scorpion\_penalty}(d) \\
&+ w_5 \cdot \text{grape\_bonus}(d) \\
&+ w_6 \cdot \text{capture\_bonus}(d) \\
&- w_7 \cdot \text{exposure\_penalty}(d)
\end{align*}
$$

**Component definitions:**

$$
\text{progress}(d) = \text{final\_pos}(d) - \text{current\_pos}
$$

$$
\text{ladder\_gain}(d) = \begin{cases}
\text{ladder\_top} - \text{landing}(d) & \text{if ladder} \\
0 & \text{otherwise}
\end{cases}
$$

$$
\text{snake\_loss}(d) = \begin{cases}
\text{landing}(d) - \text{snake\_tail} & \text{if snake} \\
0 & \text{otherwise}
\end{cases}
$$

$$
\text{scorpion\_penalty}(d) = 6 \quad \text{(3-turn tempo cost proxy)}
$$

$$
\text{grape\_bonus}(d) = \text{fixed value (represents 3-turn protection)}
$$

$$
\text{capture\_bonus}(d) = \text{opponent\_pos} - \text{nearest\_safe\_zone}(\text{opponent\_pos})
$$

$$
\text{exposure\_penalty}(d) = \text{expected demotion distance if opponent captures}
$$

**Decision rule:**

If both moves illegal $\to$ skip.

Otherwise, agent chooses:

$$
\arg\max_d \text{score}(d)
$$

 

## 13. BALANCED_EVAL

**Weights:**

$$
\begin{align*}
w_1 &= 1.0 \\
w_2 &= 2.0 \\
w_3 &= 2.5 \\
w_4 &= 1.5 \\
w_5 &= 1.5 \\
w_6 &= 2.0 \\
w_7 &= 1.5
\end{align*}
$$

**Characteristics:**
- Balanced trade-off.
- Moderately risk-averse.
- Values capture and ladders.

 

## 14. RISK_SEEKER

**Weights:**

$$
\begin{align*}
w_1 &= 1.2 \\
w_2 &= 3.0 \\
w_3 &= 1.0 \\
w_4 &= 0.5 \\
w_5 &= 0.5 \\
w_6 &= 3.0 \\
w_7 &= 0.5
\end{align*}
$$

**Characteristics:**
- High volatility.
- Aggressive capture.
- Tolerates snakes and scorpions.

 

## 15. RISK_AVERSE

**Weights:**

$$
\begin{align*}
w_1 &= 0.8 \\
w_2 &= 1.5 \\
w_3 &= 3.5 \\
w_4 &= 2.5 \\
w_5 &= 2.0 \\
w_6 &= 1.0 \\
w_7 &= 2.5
\end{align*}
$$

**Characteristics:**
- Strongly avoids punishment.
- Prioritizes safety and grapes.
- Low capture enthusiasm.


---

# Summary

**Total agents:** 15

**Agent families:**
- 3 Greedy
- 3 Risk filters
- 3 Capture-based
- 3 Status-aware
- 3 Evaluation-function-based

**Applications:**

This set produces diverse behavioral regimes suitable for:
- RL training curriculum
- LLM comparison
- Strategic diversity analysis
- Margin-based Elo ranking
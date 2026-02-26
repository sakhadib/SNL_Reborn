# Evaluation and Scoring Mechanism  
## Stochastic Adversarial Reasoning Game (SARG)

## 1. Overview

This document defines the formal evaluation protocol and rating system used to compare agents in SARG. The evaluation framework consists of:

1. Match outcome definition  
2. Margin of victory computation  
3. Expected score computation (logistic model)  
4. Margin-scaled Elo rating update  
5. Tournament aggregation protocol  

The system preserves the binary win–loss structure of classical Elo while incorporating margin-of-dominance information in a stable and bounded manner.

 

## 2. Match Outcome Definition

Each match produces exactly one of the following outcomes:

- Player A wins ($A_{\text{pos}} = 100$)
- Player B wins ($B_{\text{pos}} = 100$)

Draws are not allowed unless explicitly introduced via a maximum turn cap rule.

Let:

- Winner = $W$
- Loser = $L$
- $L_{\text{final}}$ = final board position of losing player

The binary score is defined as:

$$
\begin{align*}
S_W &= 1 \\
S_L &= 0
\end{align*}
$$  

 

## 3. Margin of Victory

To incorporate dominance information, we define the **margin of victory** as:

$$
D = 100 - L_{\text{final}}
$$

Where:

$$
\begin{align*}
L_{\text{final}} &\in \{0,1,\ldots,99\} \\
D &\in \{1,2,\ldots,100\}
\end{align*}
$$

Interpretation:

- Small $D$ → close game  
- Large $D$ → dominant victory  

For normalization:

$$
D_{\text{rel}} = \frac{D}{100}
$$

Thus:

$$
D_{\text{rel}} \in (0,1]
$$

 

## 4. Expected Score (Logistic Model)

Let $R_A$ and $R_B$ denote the current Elo ratings of players A and B.

The expected score of Player A is:

$$
E_A = \frac{1}{1 + 10^{(R_B - R_A)/400}}
$$

Similarly:

$$
E_B = 1 - E_A
$$

This preserves the standard probabilistic interpretation of Elo.

 

## 5. Margin-Scaled Elo Update

To incorporate margin information without breaking stability, we scale the K-factor.

Let:

$$
M = 1 + \alpha \cdot D_{\text{rel}}
$$

Where:

- $\alpha \in [0,1]$ controls margin sensitivity
- Recommended default: $\alpha = 0.75$

Properties:

- $M \in [1, 1 + \alpha]$
- With $\alpha = 1$ → $M \in [1,2]$
- Rating updates remain bounded

Let $K$ be the base Elo constant (recommended $K = 24$).

### Rating Update Rule

For Player A:

$$
R'_A = R_A + K \cdot M \cdot (S_A - E_A)
$$

For Player B:

$$
R'_B = R_B + K \cdot M \cdot (S_B - E_B)
$$

Since $S_A + S_B = 1$ and $E_A + E_B = 1$, the system remains zero-sum:

$$
R'_A + R'_B = R_A + R_B
$$

 

## 6. Maximum Rating Swing

Maximum update occurs when:

- Lower-rated player defeats higher-rated player
- Margin is maximal ($D_{\text{rel}} = 1$)

Maximum multiplier:

$$
M_{\text{max}} = 1 + \alpha
$$

With:

$$
\begin{align*}
K &= 24 \\
\alpha &= 1
\end{align*}
$$

Maximum theoretical swing:

$$
\Delta_{\text{max}} = 24 \times 2 \times 1 = 48
$$

This remains within stable Elo dynamics.

 

## 7. Optional Draw Rule (If Enabled)

If a maximum turn limit $T_{\text{max}}$ is imposed and exceeded:

$$
\begin{align*}
S_A &= 0.5 \\
S_B &= 0.5
\end{align*}
$$

Margin multiplier $M = 1$

Standard Elo update applies without margin scaling.

 

## 8. Tournament Protocol

### 8.1 Initialization

All agents begin with:

$$
R_{\text{initial}} = 1500
$$

### 8.2 Match Structure

For $N$ agents:

- Round-robin format
- Each pair plays $G$ games (recommended $G \geq 500$)
- Alternate starting player to remove first-move bias

### 8.3 Rating Update Timing

Ratings are updated sequentially after each game.

Alternatively, batch updating may be used but must preserve chronological ordering.

 

## 9. Statistical Reporting

Final evaluation should report:

- Final Elo ratings
- Rating confidence intervals (via bootstrap)
- Head-to-head win rates
- Margin distribution statistics
- Rating stability over time

 

## 10. Rationale

This evaluation mechanism:

1. Preserves binary win–loss structure
2. Incorporates dominance information
3. Maintains zero-sum rating integrity
4. Keeps rating updates bounded and stable
5. Avoids distortion of probabilistic interpretation

The margin-scaled Elo thus provides a more informative ranking signal for agents competing in SARG while remaining mathematically principled.
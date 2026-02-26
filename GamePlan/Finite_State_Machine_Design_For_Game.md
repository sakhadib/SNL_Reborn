# Finite State Machine (FSM) Specification  
## Stochastic Adversarial Reasoning Game (SARG)

## 1. Formal Definition

The game is modeled as a finite, fully observable, turn-based stochastic state machine:

$$
\text{FSM} = (S, A, \Omega, T, s_0, F)
$$

Where:

- $S$ = finite set of states  
- $A$ = set of actions  
- $\Omega$ = stochastic input space (dice outcomes)  
- $T: S \times A \times \Omega \to S$ = transition function  
- $s_0$ = initial state  
- $F \subset S$ = terminal states  

The system is deterministic given a state, action, and dice outcome.

 

## 2. State Space Definition

Each state $s \in S$ is defined as:

$$
s = (
    A_{\text{pos}},
    A_{\text{stun}},
    A_{\text{immune}},
    B_{\text{pos}},
    B_{\text{stun}},
    B_{\text{immune}},
    \text{turn}
)
$$

Domains:

$$
\begin{align*}
A_{\text{pos}}, B_{\text{pos}} &\in \{0,1,\ldots,100\} \\
A_{\text{stun}}, B_{\text{stun}} &\in \{0,1,2,3\} \\
A_{\text{immune}}, B_{\text{immune}} &\in \{0,1,2,3\} \\
\text{turn} &\in \{A, B\}
\end{align*}
$$  

This state fully determines future transitions.

 

## 3. State Space Size Calculation

Positions:

$$101 \times 101 = 10,201$$

Stun counters:

$$4 \times 4 = 16$$

Immunity counters:

$$4 \times 4 = 16$$

Turn indicator:

$$2$$

Total state space:

$$
\begin{align*}
|S| &= 10,201 \times 16 \times 16 \times 2 \\
|S| &= 10,201 \times 256 \times 2 \\
|S| &= 10,201 \times 512 \\
|S| &= 5,222,912
\end{align*}
$$

The system contains exactly **5,222,912** states.

 

## 4. Initial State

$$
s_0 = (0,0,0, 0,0,0, A)
$$

Player A moves first.

 

## 5. Terminal States

$$
F = \{ s \in S \mid A_{\text{pos}} = 100 \text{ or } B_{\text{pos}} = 100 \}
$$

Terminal states are absorbing:

For all $s \in F$ and all actions $a$ and dice outcomes $\omega$:

$$
T(s, a, \omega) = s
$$

 

## 6. Action Space

If current player $P$ has:

$$
P_{\text{stun}} = 0
$$

Then:

$$
A = \{ \text{choose die 1}, \text{choose die 2}, \text{skip} \}
$$

If:

$$
P_{\text{stun}} > 0
$$

Then:

$$
A = \{ \text{forced skip} \}
$$

 

## 7. Stochastic Input Space

$$
\Omega = \{ (d_1, d_2) \mid d_1 \in \{1..6\}, d_2 \in \{1..6\} \}
$$

$$
|\Omega| = 6 \times 6 = 36
$$

Dice are independent and uniformly distributed.

 

## 8. Transition Function

$$
T : S \times A \times \Omega \to S
$$

Let $P$ denote the current player.
Let $O$ denote the opponent.

### 8.1 Terminal Condition

If $s \in F$:

$$
T(s, a, \omega) = s
$$

 

### 8.2 Stun Resolution

If $P_{\text{stun}} > 0$:

$$
\begin{align*}
P'_{\text{stun}} &= P_{\text{stun}} - 1 \\
P'_{\text{immune}} &= \max(P_{\text{immune}} - 1, 0) \\
P'_{\text{pos}} &= P_{\text{pos}}
\end{align*}
$$

Opponent state unchanged.

$$
\text{turn}' = O
$$

Turn alternates even if both players are stunned.

 

### 8.3 Active Turn ($P_{\text{stun}} = 0$)

Let $\omega = (d_1, d_2)$.

If action = skip:

$$
P'_{\text{pos}} = P_{\text{pos}}
$$

Proceed to capture rule.

If action = choose_die_1:

$$d = d_1$$

If action = choose_die_2:

$$d = d_2$$

Illegal move condition:

If $P_{\text{pos}} + d > 100$:

$$
P'_{\text{pos}} = P_{\text{pos}}
$$

Proceed to capture rule.

Otherwise:

$$
\text{temp pos} = P_{\text{pos}} + d
$$

 

### 8.4 Square Effect Resolution

Let $\text{square type}(\text{temp pos})$ be defined by the fixed board.

If $P_{\text{immune}} > 0$:
Snake and scorpion effects are ignored.

Apply square type:

**Normal:**

$$P'_{\text{pos}} = \text{temp pos}$$

**Ladder:**

$$P'_{\text{pos}} = \text{ladder top}(\text{temp pos})$$

**Snake:**

If $P_{\text{immune}} = 0$:

$$P'_{\text{pos}} = \text{snake tail}(\text{temp pos})$$

Else:

$$P'_{\text{pos}} = \text{temp pos}$$

**Scorpion:**

$$P'_{\text{pos}} = \text{temp pos}$$

If $P_{\text{immune}} = 0$:

$$P'_{\text{stun}} = 3$$

**Grapes:**

$$
\begin{align*}
P'_{\text{pos}} &= \text{temp pos} \\
P'_{\text{immune}} &= 3
\end{align*}
$$

**Safe Zone:**

$$P'_{\text{pos}} = \text{temp pos}$$

If grapes not triggered:
$P'_{\text{immune}}$ remains previous value.

If scorpion not triggered:
$P'_{\text{stun}}$ remains previous value.

 

### 8.5 Win Check

If $P'_{\text{pos}} = 100$:

The state becomes terminal immediately.
Capture is not applied.

 

### 8.6 Capture Rule

If $P'_{\text{pos}} = O_{\text{pos}}$:

If $O_{\text{pos}} \in \text{SafeZones}$:
No demotion.

Else:

$$O'_{\text{pos}} = \max \{ s \in \text{SafeZones} \mid s \leq O_{\text{pos}} \}$$

Demotion does not trigger square effects.
Demotion does not alter stun or immunity.

 

### 8.7 Immunity Decay

At the end of $P$'s turn:

If $P'_{\text{immune}} > 0$:

$$P'_{\text{immune}} = P'_{\text{immune}} - 1$$

Opponent immunity unaffected.

 

### 8.8 Turn Switch

$$
\text{turn}' = O
$$

 

## 9. Determinism

For any state $s \in S$, action $a \in A$, and dice outcome $\omega \in \Omega$:

There exists exactly one $s' \in S$ such that:

$$
T(s, a, \omega) = s'
$$

The system is deterministic conditioned on dice and action.

 

## 10. Observability

The full state $s$ is observable to both players.
There are no hidden variables.
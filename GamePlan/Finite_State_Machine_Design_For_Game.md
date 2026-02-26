# Finite State Machine (FSM) Specification

## Stochastic Adversarial Reasoning Game (SARG)

 

## 1. Formal Definition

The game is modeled as a **finite, fully observable, turn-based stochastic state machine**:

[
FSM = (S, A, \Omega, T, s_0, F)
]

Where:

* ( S ) = finite set of states
* ( A ) = set of actions
* ( \Omega ) = stochastic input space (dice outcomes)
* ( T: S \times A \times \Omega \rightarrow S ) = transition function
* ( s_0 ) = initial state
* ( F \subseteq S ) = terminal states

The system is deterministic given a state, action, and dice outcome.

 

## 2. State Space Definition

Each state ( s \in S ) is defined as:

```
s = (
    A_pos,
    A_stun,
    A_immune,
    B_pos,
    B_stun,
    B_immune,
    turn
)
```

### Domains

```
A_pos, B_pos ∈ {0,1,...,100}
A_stun, B_stun ∈ {0,1,2,3}
A_immune, B_immune ∈ {0,1,2,3}
turn ∈ {A, B}
```

This state contains all necessary information to continue the game deterministically.

 

## 3. State Space Size Calculation

### Positions

[
101 \times 101 = 10,201
]

### Stun Counters

[
4 \times 4 = 16
]

### Immunity Counters

[
4 \times 4 = 16
]

### Turn Indicator

[
2
]

### Total State Space

[
|S| = 10,201 \times 16 \times 16 \times 2
]

[
= 10,201 \times 256 \times 2
]

[
= 10,201 \times 512
]

[
= 5,222,912
]

The system therefore contains exactly **5,222,912 possible states**.

The state space is finite.

 

## 4. Initial State

```
s₀ = (0,0,0, 0,0,0, A)
```

Player A starts.

 

## 5. Terminal States

[
F = { s \in S \mid A_{pos} = 100 \text{ or } B_{pos} = 100 }
]

Terminal states are absorbing:

[
T(s, a, \omega) = s \quad \forall s \in F
]

 

## 6. Action Space

If current player ( P ) has:

```
P_stun = 0
```

Then:

```
A = { choose_die_1, choose_die_2, skip }
```

If:

```
P_stun > 0
```

Then:

```
A = { forced_skip }
```

 

## 7. Stochastic Input Space

[
\Omega = { (d_1, d_2) \mid d_1, d_2 \in {1,2,3,4,5,6} }
]

[
|\Omega| = 6 \times 6 = 36
]

Dice outcomes are independent and uniformly distributed.

 

## 8. Transition Function

[
T: S \times A \times \Omega \rightarrow S
]

Let:

* ( P ) = current player
* ( O ) = opponent

 

## 8.1 Terminal Condition

If ( s \in F ):

[
T(s,a,\omega) = s
]

 

## 8.2 Stun Resolution

If:

```
P_stun > 0
```

Then:

```
P_stun'   = P_stun - 1
P_immune' = max(P_immune - 1, 0)
P_pos'    = P_pos
```

Opponent state unchanged.

```
turn' = O
```

Turn alternates even if both players are stunned.

 

## 8.3 Active Turn (P_stun = 0)

Dice outcome:

```
ω = (d1, d2)
```

### If action = skip

```
P_pos' = P_pos
```

Proceed to capture.

 

### If action selects die

```
d = d1 or d2
```

#### Illegal Move

If:

[
P_{pos} + d > 100
]

Then:

```
P_pos' = P_pos
```

Proceed to capture.

 

#### Legal Move

[
temp = P_{pos} + d
]

 

## 8.4 Square Effect Resolution

Let `square_type(temp)` be predefined by board.

If:

```
P_immune > 0
```

Snake and scorpion effects are ignored.

Apply square effect:

### Normal

```
P_pos' = temp
```

### Ladder

```
P_pos' = ladder_top(temp)
```

### Snake

If immune = 0:

```
P_pos' = snake_tail(temp)
```

Else:

```
P_pos' = temp
```

### Scorpion

```
P_pos' = temp
```

If immune = 0:

```
P_stun' = 3
```

### Grapes

```
P_pos' = temp
P_immune' = 3
```

### Safe Zone

```
P_pos' = temp
```

 

## 8.5 Win Check

If:

[
P_{pos}' = 100
]

State becomes terminal immediately.
Capture is not applied.

 

## 8.6 Capture Rule

If:

[
P_{pos}' = O_{pos}
]

Then:

If opponent position is a safe zone:

No change.

Else:

[
O_{pos}' =
\max { s \in SafeZones \mid s \le O_{pos} }
]

Demotion does not trigger square effects.

Stun and immunity counters remain unchanged.

 

## 8.7 Immunity Decay

At end of P’s turn:

If:

```
P_immune' > 0
```

Then:

```
P_immune' = P_immune' - 1
```

Opponent immunity unaffected.

 

## 8.8 Turn Switch

```
turn' = O
```

 

## 9. Determinism

For any state ( s ), action ( a ), and dice outcome ( \omega ):

[
\exists! ; s' \in S \text{ such that } T(s,a,\omega) = s'
]

The transition is uniquely determined.

 

## 10. Observability

The full state ( s ) is observable to both players.

No hidden variables exist.

 

This completes the formal FSM specification of the game.

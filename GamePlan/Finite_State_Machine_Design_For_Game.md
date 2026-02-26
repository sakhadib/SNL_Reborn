# Finite State Machine (FSM) Specification  
## Stochastic Adversarial Reasoning Game (SARG)

## 1. Formal Definition

The game is modeled as a finite, fully observable, turn-based stochastic state machine:

FSM = (S, A, Ω, T, s₀, F)

Where:

- S = finite set of states  
- A = set of actions  
- Ω = stochastic input space (dice outcomes)  
- T: S × A × Ω → S = transition function  
- s₀ = initial state  
- F ⊂ S = terminal states  

The system is deterministic given a state, action, and dice outcome.

 

## 2. State Space Definition

Each state s ∈ S is defined as:

s = (
    A_pos,
    A_stun,
    A_immune,
    B_pos,
    B_stun,
    B_immune,
    turn
)

Domains:

A_pos, B_pos ∈ {0,1,...,100}  
A_stun, B_stun ∈ {0,1,2,3}  
A_immune, B_immune ∈ {0,1,2,3}  
turn ∈ {A, B}  

This state fully determines future transitions.

 

## 3. State Space Size Calculation

Positions:
101 × 101 = 10,201

Stun counters:
4 × 4 = 16

Immunity counters:
4 × 4 = 16

Turn indicator:
2

Total state space:

|S| = 10,201 × 16 × 16 × 2  
|S| = 10,201 × 256 × 2  
|S| = 10,201 × 512  
|S| = 5,222,912

The system contains exactly 5,222,912 states.

 

## 4. Initial State

s₀ = (0,0,0, 0,0,0, A)

Player A moves first.

 

## 5. Terminal States

F = { s ∈ S | A_pos = 100 or B_pos = 100 }

Terminal states are absorbing:

For all s ∈ F and all actions a and dice outcomes ω:

T(s, a, ω) = s

 

## 6. Action Space

If current player P has:

P_stun = 0

Then:

A = { choose_die_1, choose_die_2, skip }

If:

P_stun > 0

Then:

A = { forced_skip }

 

## 7. Stochastic Input Space

Ω = { (d1, d2) | d1 ∈ {1..6}, d2 ∈ {1..6} }

|Ω| = 6 × 6 = 36

Dice are independent and uniformly distributed.

 

## 8. Transition Function

T : S × A × Ω → S

Let P denote the current player.
Let O denote the opponent.

### 8.1 Terminal Condition

If s ∈ F:

T(s, a, ω) = s

 

### 8.2 Stun Resolution

If P_stun > 0:

P_stun'   = P_stun − 1  
P_immune' = max(P_immune − 1, 0)  
P_pos'    = P_pos  

Opponent state unchanged.

turn' = O

Turn alternates even if both players are stunned.

 

### 8.3 Active Turn (P_stun = 0)

Let ω = (d1, d2).

If action = skip:

P_pos' = P_pos  
Proceed to capture rule.

If action = choose_die_1:
d = d1

If action = choose_die_2:
d = d2

Illegal move condition:

If P_pos + d > 100:

P_pos' = P_pos  
Proceed to capture rule.

Otherwise:

temp_pos = P_pos + d

 

### 8.4 Square Effect Resolution

Let square_type(temp_pos) be defined by the fixed board.

If P_immune > 0:
Snake and scorpion effects are ignored.

Apply square type:

Normal:
P_pos' = temp_pos

Ladder:
P_pos' = ladder_top(temp_pos)

Snake:
If P_immune = 0:
P_pos' = snake_tail(temp_pos)
Else:
P_pos' = temp_pos

Scorpion:
P_pos' = temp_pos
If P_immune = 0:
P_stun' = 3

Grapes:
P_pos' = temp_pos
P_immune' = 3

Safe Zone:
P_pos' = temp_pos

If grapes not triggered:
P_immune' remains previous value.

If scorpion not triggered:
P_stun' remains previous value.

 

### 8.5 Win Check

If P_pos' = 100:

The state becomes terminal immediately.
Capture is not applied.

 

### 8.6 Capture Rule

If P_pos' = O_pos:

If O_pos ∈ SafeZones:
No demotion.

Else:
O_pos' = max { s ∈ SafeZones | s ≤ O_pos }

Demotion does not trigger square effects.
Demotion does not alter stun or immunity.

 

### 8.7 Immunity Decay

At the end of P’s turn:

If P_immune' > 0:
P_immune' = P_immune' − 1

Opponent immunity unaffected.

 

### 8.8 Turn Switch

turn' = O

 

## 9. Determinism

For any state s ∈ S, action a ∈ A, and dice outcome ω ∈ Ω:

There exists exactly one s' ∈ S such that:

T(s, a, ω) = s'

The system is deterministic conditioned on dice and action.

 

## 10. Observability

The full state s is observable to both players.
There are no hidden variables.
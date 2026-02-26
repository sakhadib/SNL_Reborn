# **SARG (Stochastic Adversarial Reasoning Game)**

## **Complete Formal Rule Specification**

# **1\. Board Definition**

## **1.1 Cells**

The board consists of 101 indexed cells:  
0, 1, 2, ..., 100

*   
* Cell 0 is the starting cell.  
* Cell 100 is the terminal winning cell.

## **1.2 Square Types (Mutually Exclusive)**

Each cell belongs to exactly one of the following types:

* Normal  
* Snake  
* Ladder  
* Scorpion  
* Grapes  
* Safe Zone

No cell contains more than one type.

## **1.3 Fixed Safe Zones**

If a player occupies a safe zone:

* They cannot be demoted by capture.  
* Stacking is allowed.

## **1.4 Snakes and Ladders**

* A snake cell has a defined tail position strictly less than the snake head.  
* A ladder cell has a defined top position strictly greater than the ladder base.  
* Snake and ladder transitions are deterministic.

# **2\. Players**

Two players: Player A and Player B.

Each player has the following state:

* `position ∈ [0, 100]`  
* `stun_counter ∈ {0,1,2,3}`  
* `immunity_counter ∈ {0,1,2,3}`

Initial state for both players:

position \= 0  
stun\_counter \= 0  
immunity\_counter \= 0

Player A moves first.

# **3\. Turn Order**

Turns alternate strictly:

A → B → A → B → ...

Turn order never changes.

Turn order is independent of stun or status effects.

Even if both players are stunned, turn alternation continues.

# **4\. Turn Execution**

On a player's turn:

## **4.1 Stun Resolution**

If `stun_counter > 0`:

* The player does not roll dice.  
* The player does not move.  
* `stun_counter` decreases by 1\.  
* Immunity counter still decreases (see Section 7).  
* Turn ends immediately.  
* Control passes to opponent.

This applies even if both players are stunned.

If both are stunned:

* Each will independently skip on their respective turns.  
* Turn alternation continues normally.

There is no deadlock.

## **4.2 Dice Roll**

If `stun_counter == 0`:

Two dice are rolled:  
A ∈ {1..6}  
B ∈ {1..6}

The player must choose one of:

* Move by A  
* Move by B  
* Skip voluntarily

## **4.3 Illegal Move Rule**

If chosen dice value `d` results in:

current\_position \+ d \> 100

The move is illegal.

Illegal move results in:

* Player remains in current position.  
* No square effect is applied.  
* Turn proceeds to capture check (Section 6).  
* Turn ends.

Landing exactly on 100 wins immediately.

# **5\. Movement Resolution**

If move is legal:

New temporary position:

p \= current\_position \+ d

## **5.1 Square Effect Resolution**

Square effects are resolved in this order:

### **Step 1 — Check Immunity**

If `immunity_counter > 0`:

* Snake and scorpion effects are ignored.  
* Ladder still applies.  
* Grapes still applies.

### **Step 2 — Apply Square Type**

Depending on square type at position `p`:

### **Normal**

No change.

### **Ladder**

Move to ladder top immediately.

### **Snake**

If not immune:

* Move to snake tail.

If immune:

* Remain at `p`.

### **Scorpion**

If not immune:

* Set `stun_counter = 3`

If immune:

* No stun applied.

### **Grapes**

* Set `immunity_counter = 3`

### **Safe Zone**

No special effect beyond capture immunity.

All transitions are applied fully before capture check.

# **6\. Capture Rule**

After all movement and square effects are fully resolved:

If active player's final position equals opponent’s position:

### **Case 1 — Opponent is on Safe Zone**

* No demotion occurs.  
* Both players stack.  
* No further effect.

### **Case 2 — Opponent is NOT on Safe Zone**

Opponent is demoted to:

max{s ∈ SafeZones | s ≤ opponent\_position}

Demotion does NOT trigger square effects.

Demotion does NOT trigger snake, ladder, grapes, or scorpion.

Demotion does NOT grant immunity or stun.

Demotion is a pure relocation.

# **7\. Immunity Counter Decay**

At the end of each player’s turn (including skipped turns due to stun):

If `immunity_counter > 0`:

`immunity_counter -= 1`

Immunity lasts exactly 3 of that player's turns.

Opponent turns do not affect immunity duration.

# **8\. Win Condition**

A player wins immediately if:

position \== 100

Game terminates instantly.

No capture occurs after a win.

If landing on 100 triggers capture:

* Win condition takes precedence.  
* Game ends immediately.

# **9\. Special Edge Case Clarifications**

### **9.1 Both Players Stunned**

If:

* Player A stun\_counter \> 0  
* Player B stun\_counter \> 0

Turns alternate normally.

Example:

Turn A → skip → A stun=2  
Turn B → skip → B stun=2  
Turn A → skip → A stun=1  
Turn B → skip → B stun=1

No deadlock possible.

### **9.2 Stunned Player Gets Captured**

If a stunned player is captured:

* They are demoted normally.  
* Stun counter remains unchanged.  
* They continue serving stun.

### **9.3 Capturing a Stunned Player**

Capture works normally.  
Capturing player does not inherit stun.

### **9.4 Capturing an Immune Player**

Immunity does not protect from capture.

Only safe zones protect from capture.

### **9.5 Grapes While Already Immune**

If a player with immunity lands on grapes:

immunity\_counter \= 3

It resets to 3 (does not stack to 6).

### **9.6 Scorpion While Already Stunned**

If a stunned player lands on scorpion (possible only via capture demotion):

No additional stun is added.

Stun counter does not stack.

### **9.7 Demotion to Safe Zone**

Demotion never triggers square effects.

Even if demoted onto:

* grapes  
* scorpion  
* snake  
* ladder

No effect applies.

Safe zone demotion is effect-neutral.

# **10\. Determinism Guarantee**

Given:

* Board layout  
* Dice outcomes  
* Player decisions

The game is fully deterministic.

There are no hidden states.

# **11\. State Completeness**

Complete game state is:

(  
  A\_position,  
  A\_stun\_counter,  
  A\_immunity\_counter,  
  B\_position,  
  B\_stun\_counter,  
  B\_immunity\_counter,  
  turn\_indicator  
)
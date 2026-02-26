Assume the engine provides helper functions:

* `legal(d)`
* `landing(d)`
* `final_pos(d)`  (after snake/ladder/scorpion/grapes but before capture)
* `is_snake(d)`
* `is_scorpion(d)`
* `is_grape(d)`
* `is_safe(d)`
* `captures(d)`
* `opponent_can_capture(pos)`
* `progress(d) = final_pos(d) - current_pos`

If both dice illegal → return `skip`.

We denote dice as `d1`, `d2`.

 

# 1. MAXIM

**Idea:** Pure forward greed.

### Pseudocode

```
if legal(d1) and legal(d2):
    return die with larger value
elif legal(d1):
    return d1
elif legal(d2):
    return d2
else:
    return skip
```

**Behavior:** Aggressive. Ignores risk.

 

# 2. MINIM

**Idea:** Minimal forward exposure.

### Pseudocode

```
if legal(d1) and legal(d2):
    return die with smaller value
elif legal(d1):
    return d1
elif legal(d2):
    return d2
else:
    return skip
```

**Behavior:** Conservative baseline.

 

# 3. EXACTOR

**Idea:** Endgame precision.

### Pseudocode

```
if legal(d1) and landing(d1) == 100:
    return d1
if legal(d2) and landing(d2) == 100:
    return d2
return MAXIM policy
```

**Behavior:** Same as MAXIM except exact-win priority.

 

# 4. SNAKE_AVOIDER

**Idea:** Avoid demotion if possible.

### Pseudocode

```
safe_moves = []
for d in [d1, d2]:
    if legal(d) and not is_snake(d):
        safe_moves.append(d)

if safe_moves not empty:
    return largest in safe_moves

if legal(d1) and legal(d2):
    return smaller(d1, d2)

return skip
```

**Behavior:** Penalizes snake heads.

 

# 5. SCORPION_AVOIDER

**Idea:** Avoid tempo loss.

### Pseudocode

```
safe_moves = []
for d in [d1, d2]:
    if legal(d) and not is_scorpion(d):
        safe_moves.append(d)

if safe_moves not empty:
    return largest in safe_moves

if legal(d1) and legal(d2):
    return smaller(d1, d2)

return skip
```

**Behavior:** Stun minimizer.

 

# 6. SAFE_PREFERRER

**Idea:** Anchor on safe zones.

### Pseudocode

```
for d in [d1, d2]:
    if legal(d) and is_safe(d):
        return d

return SNAKE_AVOIDER policy
```

**Behavior:** Defensive positional anchor.

 

# 7. HUNTER

**Idea:** Aggressive capture.

### Pseudocode

```
for d in [d1, d2]:
    if legal(d) and captures(d):
        return d

return MAXIM policy
```

**Behavior:** Always prioritizes capture.

 

# 8. SAFE_HUNTER

**Idea:** Smart capture.

### Pseudocode

```
for d in [d1, d2]:
    if legal(d) and captures(d) and opponent not near safe zone:
        return d

return SNAKE_AVOIDER policy
```

**Behavior:** Avoids useless captures.

 

# 9. ANTI_CAPTURE

**Idea:** Avoid exposure.

### Pseudocode

```
safe_moves = []
for d in [d1, d2]:
    if legal(d) and not opponent_can_capture(final_pos(d)):
        safe_moves.append(d)

if safe_moves not empty:
    return largest in safe_moves

if legal(d1) and legal(d2):
    return smaller(d1, d2)

return skip
```

**Behavior:** One-step opponent modeling.

 

# 10. GRAPE_SEEKER

**Idea:** Prioritize immunity.

### Pseudocode

```
for d in [d1, d2]:
    if legal(d) and is_grape(d):
        return d

return SNAKE_AVOIDER policy
```

**Behavior:** Timing-based immunity play.

 

# 11. IMMUNE_AGGRESSOR

**Idea:** Use immunity window.

### Pseudocode

```
if immunity_counter > 0:
    return MAXIM policy
else:
    return SNAKE_AVOIDER policy
```

**Behavior:** Risk-on when immune.

 

# 12. STUN_EXPLOITER

**Idea:** Exploit tempo advantage.

### Pseudocode

```
if opponent_stun > 0:
    return MAXIM policy
else:
    return SCORPION_AVOIDER policy
```

**Behavior:** Aggressive only when opponent frozen.

 

# 13. BALANCED_EVAL

**Idea:** Weighted evaluation function.

### Score Definition

For legal d:

```
score(d) =
    1.0 * progress(d)
  + 2.0 * ladder_gain(d)
  - 2.5 * snake_loss(d)
  - 1.5 * scorpion_penalty(d)
  + 1.5 * grape_bonus(d)
  + 2.0 * capture_bonus(d)
  - 1.5 * exposure_penalty(d)
```

### Pseudocode

```
best_score = -infinity
best_move = skip

for d in [d1, d2]:
    if legal(d):
        s = compute_score(d)
        if s > best_score:
            best_score = s
            best_move = d

return best_move
```

**Behavior:** Generalist.

 

# 14. RISK_SEEKER

**Idea:** Volatility maximizer.

### Score

```
score(d) =
    1.2 * progress(d)
  + 3.0 * ladder_gain(d)
  - 1.0 * snake_loss(d)
  - 0.5 * scorpion_penalty(d)
  + 0.5 * grape_bonus(d)
  + 3.0 * capture_bonus(d)
  - 0.5 * exposure_penalty(d)
```

**Behavior:** Aggressive, high swing.

 

# 15. RISK_AVERSE

**Idea:** Minimize punishment.

### Score

```
score(d) =
    0.8 * progress(d)
  + 1.5 * ladder_gain(d)
  - 3.5 * snake_loss(d)
  - 2.5 * scorpion_penalty(d)
  + 2.0 * grape_bonus(d)
  + 1.0 * capture_bonus(d)
  - 2.5 * exposure_penalty(d)
```

**Behavior:** Defensive planner.
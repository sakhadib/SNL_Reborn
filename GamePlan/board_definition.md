# Board Specification  
## Stochastic Adversarial Reasoning Game (SARG)  
### Version 1.0 (Strategic Asymmetric Acceleration–Punishment Design)

This board is designed under the following game-theoretic principles:

1. Early acceleration with bounded punishment.
2. Mid-game volatility enabling tactical interaction.
3. Late-game high-risk, high-precision dynamics.
4. Asymmetric but non-snowballing progression.
5. Structured comeback potential.
6. Sparse but impactful tempo-disruption (scorpion) mechanics.
7. Immunity timing windows before high-risk regions.
8. Mutually exclusive square types.

All square types are mutually exclusive.  
No square simultaneously contains more than one of the following:

- Ladder base  
- Ladder top  
- Snake head  
- Snake tail  
- Scorpion  
- Grapes  
- Safe zone  

 

## 1. Safe Zones

Safe zones provide immunity from capture demotion.

$$
\text{SafeZones} = \{0, 18, 41, 63, 86\}
$$

Properties:
- Irregular spacing creates tactical asymmetry.
- Safe zones act as defensive anchors.
- Demotion always relocates to the greatest safe zone less than or equal to the current position.

 

## 2. Ladders

Ladders promote upward movement.

Total ladders: 7

| Base | Top |
| ---- | --- |
| 4    | 14  |
| 9    | 23  |
| 15   | 34  |
| 27   | 48  |
| 36   | 58  |
| 52   | 68  |
| 71   | 83  |

Design properties:
- Concentrated primarily in the 0–50 region.
- Magnitude gradually increases in early region.
- Only two ladders exist beyond position 50.
- No ladder base or top overlaps with any other special square.
- No ladder top directly lands on a snake head.

 

## 3. Snakes

Snakes demote position downward.

Total snakes: 8

| Head | Tail |
| ---- | ---- |
| 22   | 11   |
| 31   | 19   |
| 44   | 29   |
| 57   | 38   |
| 69   | 47   |
| 78   | 54   |
| 92   | 61   |
| 97   | 72   |

Design properties:
- Early snakes are mild.
- Post-60 snakes increase in magnitude.
- 92 and 97 serve as major late-game punishment nodes.
- No snake head coincides with ladder tops, safe zones, grapes, or scorpions.
- Snake tails do not create chained forced demotions.

 

## 4. Scorpions

Landing on a scorpion induces a 3-turn stun unless immune.

Total scorpions: 6

$$
\text{ScorpionSquares} = \{6, 20, 33, 46, 62, 74\}
$$

Distribution:
- Four in 0–50 region.
- Two in 50–100 region.

Design properties:
- Early tempo disruption.
- Mid-game swing potential.
- No scorpion overlaps with ladder bases, ladder tops, snake heads, snake tails, grapes, or safe zones.

 

## 5. Grapes

Landing on grapes grants 3-turn immunity from snakes and scorpions.

Total grapes: 4

$$
\text{GrapeSquares} = \{39, 55, 76, 88\}
$$

Distribution:
- One in early-mid region.
- Three in 50–100 region.

Design properties:
- 55 precedes the 57 snake.
- 76 precedes the 78 snake.
- 88 precedes the 92 and 97 late snakes.
- Encourages timing-based strategic planning.
- No overlap with any other square type.

 

## 6. Normal Squares

All remaining squares not listed above are normal squares.

 

## 7. Mutual Exclusivity Constraint

Let:

$$
\begin{align*}
\text{SpecialSquares} =\, &\text{SafeZones} \cup \\
&\text{LadderBases} \cup \text{LadderTops} \cup \\
&\text{SnakeHeads} \cup \text{SnakeTails} \cup \\
&\text{ScorpionSquares} \cup \\
&\text{GrapeSquares}
\end{align*}
$$

Constraint:

For all $x \in \{0,\ldots,100\}$, $x$ belongs to at most one category.

This ensures deterministic and conflict-free state transitions.

 

## 8. Structural Game-Theoretic Properties

This board satisfies:

- Early mobility advantage without deterministic snowball.
- Mid-board volatility enabling capture dynamics.
- Late-game risk amplification requiring precision.
- Strategic immunity timing windows.
- Defensive anchoring through irregular safe zones.
- Non-trivial decision surface for heuristic, RL, and LLM agents.

 

## 9. Canonical Board Definition

This configuration is designated as:

SARG Board v1.0 (Canonical)

All experimental evaluations must reference this exact board configuration unless explicitly conducting ablation or variant analysis.
# Game and Move Storage Specification  
## Stochastic Adversarial Reasoning Game (SARG)  
### Version 1.0 — Binary Reproducible Format

This document formalizes the storage design for large-scale simulation of SARG games.  
The format is optimized for:

- Full deterministic reproducibility
- Efficient storage of 100M+ games
- Fast sequential write
- Random-access replay
- Opportunity-cost and counterfactual analysis
- NN / RL dataset extraction

The format is append-only, binary, and deterministic.

 -

# 1. Design Principles

1. Minimal Sufficient Information  
   Only store data required to reconstruct the game exactly.

2. Deterministic Replay  
   Given:
   - Board version
   - Initial state
   - Dice outcomes per move
   - Chosen action per move  
   The full game must be replayable without ambiguity.

3. Derived State  
   No intermediate state variables (positions, stuns, captures, etc.) are stored.
   All state transitions are recomputed during replay.

4. Fixed-Width Encoding  
   All headers and moves use fixed-width encoding for constant-time indexing.

5. Future-Proofing  
   Reserved bits are included for backward-compatible upgrades.

 -

# 2. Storage Hierarchy

Binary file structure:

[ FILE HEADER ]
[ GAME HEADER ]
[ MOVE 1 ]
[ MOVE 2 ]
...
[ MOVE N ]
[ GAME HEADER ]
...

Games are stored sequentially in append-only format.

An optional separate index file maps game_id → byte offset.

 -

# 3. Deterministic Reproducibility Requirements

To reproduce a game exactly, the following are required:

- Board version identifier
- Ordered sequence of (d1, d2, action)
- Fixed initial state (A_pos=0, B_pos=0, no stun, no immunity)

No RNG seed is required because dice are explicitly stored.

 -

# 4. File Header (Fixed 16 Bytes)

| Field             | Size (bytes) |
|------------------|--------------|
| Magic Number      | 4            |
| Format Version    | 1            |
| Board Version     | 1            |
| Reserved          | 10           |

Magic Number: 4-byte constant (e.g., "SARG")  
Format Version: storage format version  
Board Version: identifies board configuration  
Reserved: future extension

Total: 16 bytes

 -

# 5. Game Header (Fixed 16 Bytes)

| Field              | Size (bytes) |
|-------------------|--------------|
| Player A ID       | 1            |
| Player B ID       | 1            |
| Winner            | 1            |
| Move Count        | 2            |
| Reserved          | 11           |

Winner:
0 = Player A  
1 = Player B  

Move Count:
Unsigned 16-bit integer (max 65535 moves per game)

Reserved:
Future extensions (Elo delta, seed, etc.)

Total: 16 bytes

 -

# 6. Move Encoding (Fixed 2 Bytes Per Move)

Each move stores:

- Dice outcome 1
- Dice outcome 2
- Chosen action

All square effects are recomputed during replay.

## 6.1 Bit Layout (16 Bits Total)

Byte 1:

Bits 0–2: d1  (3 bits, values 1–6)  
Bits 3–5: d2  (3 bits, values 1–6)  
Bits 6–7: action (2 bits)

Byte 2:

Bits 0–7: reserved (8 bits)

## 6.2 Action Encoding

0 → choose_die_1  
1 → choose_die_2  
2 → skip  
3 → reserved (unused)

## 6.3 Why 16 Bits?

Although only 8–10 bits are required, 16-bit alignment:

- Simplifies memory alignment
- Improves I/O performance
- Avoids complex bit-shifting errors
- Allows future extensions

 -

# 7. Game Size Estimation

Assume:

Average moves per game = 60

Per game storage:

Move data: 60 × 2 bytes = 120 bytes  
Game header: 16 bytes  
Total ≈ 136 bytes per game

For 100M games:

100,000,000 × 136 bytes ≈ 13.6 GB

This fits comfortably within modern storage systems.

 -

# 8. Index File (Optional but Recommended)

Separate binary file:

For each game:

| Field        | Size |
|-------------|------|
| File Offset | 8 B  |
| Move Count  | 2 B  |

Total: 10 bytes per game

Allows:

- O(1) random game access
- Fast mini-batch sampling for NN
- Efficient replay

For 100M games:

100M × 10 bytes = 1 GB index file

 -

# 9. Replay Procedure

To reconstruct a game:

1. Initialize state:
   - A_pos = 0
   - B_pos = 0
   - stun = 0
   - immunity = 0
   - turn = A

2. For each stored move:
   - Read d1, d2, action
   - Apply action
   - Apply square effects
   - Apply capture
   - Update stun/immunity
   - Switch turn

3. Stop after move_count moves.

Replay must be fully deterministic.

 -

# 10. Opportunity Cost and Counterfactual Analysis

Because both dice are stored, for every move we can compute:

- Chosen action value
- Unchosen action value
- Immediate regret
- Long-term margin difference (via replay)
- Policy disagreement between agents

This enables:

- Regret analysis
- RL vs LLM comparison
- Strategic mistake profiling
- Counterfactual evaluation

 -

# 11. Integrity Requirements

All implementations must include:

- Replay validation test
- Encode → Decode → Replay consistency check
- Deterministic hash validation per file (optional checksum)

Before scaling beyond 1M games, validation must confirm:

- No move corruption
- No misalignment
- No desynchronization

 -

# 12. Versioning Policy

If any of the following change:

- Board layout
- Move encoding format
- Game rules

Board Version and/or Format Version must be incremented.

Backward compatibility must be preserved where possible.

 -

# 13. Summary

This binary storage format ensures:

- Full deterministic reproducibility
- Minimal storage overhead
- Efficient 100M+ game logging
- Counterfactual analysis capability
- Clean separation between game simulation and learning pipeline

This specification is designated:

SARG Binary Game Format v1.0
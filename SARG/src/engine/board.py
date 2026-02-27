"""
Board Definition - SARG Canonical Board v1.0
This is the source of truth for the game board configuration.
"""

from typing import Dict, List, Optional, Set, Tuple
from .enums import SquareType, MIN_POSITION, MAX_POSITION


class Board:
    """
    SARG Canonical Board v1.0
    
    Immutable board configuration defining:
    - Safe zones
    - Ladders (base -> top)
    - Snakes (head -> tail)
    - Scorpions (stun squares)
    - Grapes (immunity squares)
    
    All square types are mutually exclusive.
    """
    
    VERSION = "1.0"
    
    # Safe Zones: Immunity from capture demotion
    SAFE_ZONES: Set[int] = {0, 18, 41, 63, 86}
    
    # Ladders: (base, top) - promote upward
    LADDERS: List[Tuple[int, int]] = [
        (4, 14),
        (9, 23),
        (15, 34),
        (27, 48),
        (36, 58),
        (52, 68),
        (71, 83),
    ]
    
    # Snakes: (head, tail) - demote downward
    SNAKES: List[Tuple[int, int]] = [
        (22, 11),
        (31, 19),
        (44, 29),
        (57, 38),
        (69, 47),
        (78, 54),
        (92, 61),
        (97, 72),
    ]
    
    # Scorpions: Landing induces 3-turn stun (unless immune)
    SCORPIONS: Set[int] = {6, 20, 33, 46, 62, 74}
    
    # Grapes: Landing grants 3-turn immunity
    GRAPES: Set[int] = {39, 55, 76, 88}
    
    def __init__(self):
        """Initialize board with validation and lookup tables."""
        self._validate_board()
        self._build_lookup_tables()
    
    def _validate_board(self) -> None:
        """Validate that board configuration satisfies all constraints."""
        # Check position ranges
        assert all(0 <= pos <= MAX_POSITION for pos in self.SAFE_ZONES)
        assert all(MIN_POSITION <= pos <= MAX_POSITION for pos in self.SCORPIONS)
        assert all(MIN_POSITION <= pos <= MAX_POSITION for pos in self.GRAPES)
        
        # Check ladder validity
        for base, top in self.LADDERS:
            assert MIN_POSITION <= base < top <= MAX_POSITION, \
                f"Invalid ladder: {base} -> {top}"
        
        # Check snake validity
        for head, tail in self.SNAKES:
            assert MIN_POSITION <= tail < head <= MAX_POSITION, \
                f"Invalid snake: {head} -> {tail}"
        
        # Check mutual exclusivity
        all_special: Set[int] = set()
        
        # Add all special squares
        all_special.update(self.SAFE_ZONES)
        all_special.update([base for base, _ in self.LADDERS])
        all_special.update([top for _, top in self.LADDERS])
        all_special.update([head for head, _ in self.SNAKES])
        all_special.update([tail for _, tail in self.SNAKES])
        all_special.update(self.SCORPIONS)
        all_special.update(self.GRAPES)
        
        # Count total distinct positions
        counts: Dict[int, int] = {}
        for pos in self.SAFE_ZONES:
            counts[pos] = counts.get(pos, 0) + 1
        for base, top in self.LADDERS:
            counts[base] = counts.get(base, 0) + 1
            counts[top] = counts.get(top, 0) + 1
        for head, tail in self.SNAKES:
            counts[head] = counts.get(head, 0) + 1
            counts[tail] = counts.get(tail, 0) + 1
        for pos in self.SCORPIONS:
            counts[pos] = counts.get(pos, 0) + 1
        for pos in self.GRAPES:
            counts[pos] = counts.get(pos, 0) + 1
        
        # Verify no overlaps (each position appears at most once)
        duplicates = {pos: count for pos, count in counts.items() if count > 1}
        assert not duplicates, f"Overlapping square types at positions: {duplicates}"
    
    def _build_lookup_tables(self) -> None:
        """Build efficient lookup tables for game engine."""
        # Ladder lookup: base -> top
        self._ladder_map: Dict[int, int] = {base: top for base, top in self.LADDERS}
        
        # Snake lookup: head -> tail
        self._snake_map: Dict[int, int] = {head: tail for head, tail in self.SNAKES}
        
        # Square type lookup
        self._square_types: Dict[int, SquareType] = {}
        
        # Build complete square type map
        for pos in range(MIN_POSITION, MAX_POSITION + 1):
            if pos in self.SAFE_ZONES:
                self._square_types[pos] = SquareType.SAFE_ZONE
            elif pos in self._ladder_map:
                self._square_types[pos] = SquareType.LADDER_BASE
            elif pos in [top for _, top in self.LADDERS]:
                self._square_types[pos] = SquareType.LADDER_TOP
            elif pos in self._snake_map:
                self._square_types[pos] = SquareType.SNAKE_HEAD
            elif pos in [tail for _, tail in self.SNAKES]:
                self._square_types[pos] = SquareType.SNAKE_TAIL
            elif pos in self.SCORPIONS:
                self._square_types[pos] = SquareType.SCORPION
            elif pos in self.GRAPES:
                self._square_types[pos] = SquareType.GRAPES
            else:
                self._square_types[pos] = SquareType.NORMAL
    
    def get_square_type(self, position: int) -> SquareType:
        """Get the type of square at a position."""
        return self._square_types[position]
    
    def is_safe_zone(self, position: int) -> bool:
        """Check if position is a safe zone."""
        return position in self.SAFE_ZONES
    
    def is_ladder(self, position: int) -> bool:
        """Check if position is a ladder base."""
        return position in self._ladder_map
    
    def is_snake(self, position: int) -> bool:
        """Check if position is a snake head."""
        return position in self._snake_map
    
    def is_scorpion(self, position: int) -> bool:
        """Check if position has a scorpion."""
        return position in self.SCORPIONS
    
    def is_grapes(self, position: int) -> bool:
        """Check if position has grapes."""
        return position in self.GRAPES
    
    def get_ladder_top(self, position: int) -> Optional[int]:
        """Get ladder top if position is a ladder base, None otherwise."""
        return self._ladder_map.get(position)
    
    def get_snake_tail(self, position: int) -> Optional[int]:
        """Get snake tail if position is a snake head, None otherwise."""
        return self._snake_map.get(position)
    
    def get_previous_safe_zone(self, position: int) -> int:
        """
        Get the greatest safe zone <= position.
        Used for capture demotion.
        """
        valid_safe_zones = [sz for sz in self.SAFE_ZONES if sz <= position]
        return max(valid_safe_zones) if valid_safe_zones else 0
    
    def __repr__(self) -> str:
        return f"Board(version={self.VERSION})"
    
    def print_board_info(self) -> None:
        """Print comprehensive board information."""
        print(f"╔══════════════════════════════════════════════════════╗")
        print(f"║  SARG Canonical Board v{self.VERSION}                       ║")
        print(f"╚══════════════════════════════════════════════════════╝")
        print()
        print(f"Safe Zones ({len(self.SAFE_ZONES)}): {sorted(self.SAFE_ZONES)}")
        print()
        print(f"Ladders ({len(self.LADDERS)}):")
        for base, top in self.LADDERS:
            gain = top - base
            print(f"  {base:3d} → {top:3d} (+{gain:2d})")
        print()
        print(f"Snakes ({len(self.SNAKES)}):")
        for head, tail in self.SNAKES:
            loss = head - tail
            print(f"  {head:3d} → {tail:3d} (-{loss:2d})")
        print()
        print(f"Scorpions ({len(self.SCORPIONS)}): {sorted(self.SCORPIONS)}")
        print()
        print(f"Grapes ({len(self.GRAPES)}): {sorted(self.GRAPES)}")
        print()


# Global canonical board instance
CANONICAL_BOARD = Board()

"""
Enumerations and constants for SARG game engine.
"""

from enum import Enum, IntEnum


class Player(IntEnum):
    """Player identifier."""
    A = 0
    B = 1
    
    def opponent(self) -> 'Player':
        """Return the opponent player."""
        return Player.B if self == Player.A else Player.A
    
    def __str__(self) -> str:
        return "Player A" if self == Player.A else "Player B"


class Action(IntEnum):
    """Action encoding for moves."""
    CHOOSE_DIE_1 = 0
    CHOOSE_DIE_2 = 1
    SKIP = 2
    
    def __str__(self) -> str:
        if self == Action.CHOOSE_DIE_1:
            return "Choose Die 1"
        elif self == Action.CHOOSE_DIE_2:
            return "Choose Die 2"
        else:
            return "Skip"


class SquareType(Enum):
    """Type of board square."""
    NORMAL = "normal"
    LADDER_BASE = "ladder_base"
    LADDER_TOP = "ladder_top"
    SNAKE_HEAD = "snake_head"
    SNAKE_TAIL = "snake_tail"
    SCORPION = "scorpion"
    GRAPES = "grapes"
    SAFE_ZONE = "safe_zone"
    
    def __str__(self) -> str:
        return self.value.replace('_', ' ').title()


# Game constants
MIN_POSITION = 0
MAX_POSITION = 100
WINNING_POSITION = 100
MAX_STUN_COUNTER = 3
MAX_IMMUNITY_COUNTER = 3
MIN_DICE = 1
MAX_DICE = 6

# State space size (for reference)
# 101 positions * 101 positions * 4 stun * 4 stun * 4 immune * 4 immune * 2 turns
STATE_SPACE_SIZE = 101 * 101 * 4 * 4 * 4 * 4 * 2  # = 5,222,912

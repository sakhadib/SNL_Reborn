"""
Game State - Immutable state representation with full validation.
"""

from dataclasses import dataclass
from typing import Optional
from .enums import Player, MIN_POSITION, MAX_POSITION, WINNING_POSITION
from .board import Board, CANONICAL_BOARD


@dataclass(frozen=True)
class GameState:
    """
    Immutable game state representation.
    
    Complete state consists of:
    - Positions for both players (0-100)
    - Stun counters (0-3)
    - Immunity counters (0-3)
    - Current turn indicator
    - Board configuration (reference)
    """
    
    # Player A state
    a_position: int
    a_stun: int
    a_immunity: int
    
    # Player B state
    b_position: int
    b_stun: int
    b_immunity: int
    
    # Turn state
    current_player: Player
    
    # Board reference
    board: Board = CANONICAL_BOARD
    
    def __post_init__(self):
        """Validate state after initialization."""
        self._validate()
    
    def _validate(self) -> None:
        """Validate all state components."""
        # Validate positions
        assert MIN_POSITION <= self.a_position <= MAX_POSITION, \
            f"Invalid Player A position: {self.a_position}"
        assert MIN_POSITION <= self.b_position <= MAX_POSITION, \
            f"Invalid Player B position: {self.b_position}"
        
        # Validate stun counters
        assert 0 <= self.a_stun <= 3, f"Invalid Player A stun: {self.a_stun}"
        assert 0 <= self.b_stun <= 3, f"Invalid Player B stun: {self.b_stun}"
        
        # Validate immunity counters
        assert 0 <= self.a_immunity <= 3, f"Invalid Player A immunity: {self.a_immunity}"
        assert 0 <= self.b_immunity <= 3, f"Invalid Player B immunity: {self.b_immunity}"
        
        # Validate current player
        assert self.current_player in [Player.A, Player.B], \
            f"Invalid current player: {self.current_player}"
    
    @classmethod
    def initial_state(cls, board: Optional[Board] = None) -> 'GameState':
        """
        Create initial game state.
        Both players start at position 0, Player A goes first.
        """
        return cls(
            a_position=0,
            a_stun=0,
            a_immunity=0,
            b_position=0,
            b_stun=0,
            b_immunity=0,
            current_player=Player.A,
            board=board or CANONICAL_BOARD
        )
    
    def get_player_position(self, player: Player) -> int:
        """Get position of specified player."""
        return self.a_position if player == Player.A else self.b_position
    
    def get_player_stun(self, player: Player) -> int:
        """Get stun counter of specified player."""
        return self.a_stun if player == Player.A else self.b_stun
    
    def get_player_immunity(self, player: Player) -> int:
        """Get immunity counter of specified player."""
        return self.a_immunity if player == Player.A else self.b_immunity
    
    def is_terminal(self) -> bool:
        """Check if game has ended (someone reached position 100)."""
        return self.a_position == WINNING_POSITION or self.b_position == WINNING_POSITION
    
    def get_winner(self) -> Optional[Player]:
        """Return winner if game is terminal, None otherwise."""
        if self.a_position == WINNING_POSITION:
            return Player.A
        elif self.b_position == WINNING_POSITION:
            return Player.B
        return None
    
    def get_loser_final_position(self) -> Optional[int]:
        """Return loser's final position if game is terminal, None otherwise."""
        winner = self.get_winner()
        if winner is None:
            return None
        loser = winner.opponent()
        return self.get_player_position(loser)
    
    def is_player_stunned(self, player: Player) -> bool:
        """Check if player is currently stunned."""
        return self.get_player_stun(player) > 0
    
    def is_player_immune(self, player: Player) -> bool:
        """Check if player is currently immune."""
        return self.get_player_immunity(player) > 0
    
    def update(
        self,
        a_position: Optional[int] = None,
        a_stun: Optional[int] = None,
        a_immunity: Optional[int] = None,
        b_position: Optional[int] = None,
        b_stun: Optional[int] = None,
        b_immunity: Optional[int] = None,
        current_player: Optional[Player] = None,
    ) -> 'GameState':
        """
        Create a new GameState with updated values.
        Immutable update pattern.
        """
        return GameState(
            a_position=a_position if a_position is not None else self.a_position,
            a_stun=a_stun if a_stun is not None else self.a_stun,
            a_immunity=a_immunity if a_immunity is not None else self.a_immunity,
            b_position=b_position if b_position is not None else self.b_position,
            b_stun=b_stun if b_stun is not None else self.b_stun,
            b_immunity=b_immunity if b_immunity is not None else self.b_immunity,
            current_player=current_player if current_player is not None else self.current_player,
            board=self.board
        )
    
    def to_dict(self) -> dict:
        """Convert state to dictionary for serialization."""
        return {
            'a_position': self.a_position,
            'a_stun': self.a_stun,
            'a_immunity': self.a_immunity,
            'b_position': self.b_position,
            'b_stun': self.b_stun,
            'b_immunity': self.b_immunity,
            'current_player': self.current_player.value,
            'board_version': self.board.VERSION
        }
    
    def __str__(self) -> str:
        """Human-readable state representation."""
        winner = self.get_winner()
        status = f"GAME OVER - {winner} wins!" if winner else "In Progress"
        
        return (
            f"GameState(turn={self.current_player}, status={status})\n"
            f"  Player A: pos={self.a_position:3d}, stun={self.a_stun}, immune={self.a_immunity}\n"
            f"  Player B: pos={self.b_position:3d}, stun={self.b_stun}, immune={self.b_immunity}"
        )
    
    def pretty_print(self) -> None:
        """Print detailed formatted state."""
        winner = self.get_winner()
        
        print("╔═══════════════════════════════════════════╗")
        print("║           GAME STATE                      ║")
        print("╠═══════════════════════════════════════════╣")
        
        if winner:
            print(f"║  Status: GAME OVER - {winner} WINS!{' ' * (10 if winner == Player.A else 9)}║")
        else:
            print(f"║  Status: In Progress                      ║")
        
        print(f"║  Current Turn: {self.current_player}{' ' * (26 if self.current_player == Player.A else 25)}║")
        print("╠═══════════════════════════════════════════╣")
        print("║  Player A                                 ║")
        print(f"║    Position: {self.a_position:3d}{' ' * (28 if self.a_position < 100 else 27)}║")
        print(f"║    Stun Counter: {self.a_stun}                       ║")
        print(f"║    Immunity Counter: {self.a_immunity}                   ║")
        
        if self.board.is_safe_zone(self.a_position):
            print("║    On SAFE ZONE                           ║")
        
        print("╠═══════════════════════════════════════════╣")
        print("║  Player B                                 ║")
        print(f"║    Position: {self.b_position:3d}{' ' * (28 if self.b_position < 100 else 27)}║")
        print(f"║    Stun Counter: {self.b_stun}                       ║")
        print(f"║    Immunity Counter: {self.b_immunity}                   ║")
        
        if self.board.is_safe_zone(self.b_position):
            print("║    On SAFE ZONE                           ║")
        
        print("╚═══════════════════════════════════════════╝")

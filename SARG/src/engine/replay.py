"""
Game Replay System - Track and visualize complete game history.
"""

from typing import List, Optional, Tuple, TYPE_CHECKING
from dataclasses import dataclass, field
if TYPE_CHECKING:
    from .game_engine import MoveInfo
from .game_state import GameState
from .board import Board, CANONICAL_BOARD
from .enums import Player, Action


@dataclass
class GameReplay:
    """
    Complete game replay with move history.
    Can reconstruct any point in the game.
    """
    initial_state: GameState
    moves: List['MoveInfo'] = field(default_factory=list)
    board: Board = CANONICAL_BOARD
    
    def add_move(self, move_info: 'MoveInfo') -> None:
        """Add a move to the replay history."""
        self.moves.append(move_info)
    
    def get_final_state(self) -> GameState:
        """Get the final state of the game."""
        if not self.moves:
            return self.initial_state
        return self.moves[-1].final_state
    
    def get_state_at_move(self, move_number: int) -> GameState:
        """Get state after specified move number (0-indexed)."""
        if move_number < 0:
            return self.initial_state
        if move_number >= len(self.moves):
            return self.get_final_state()
        return self.moves[move_number].final_state
    
    def get_move_count(self) -> int:
        """Get total number of moves in the game."""
        return len(self.moves)
    
    def get_winner(self) -> Optional[Player]:
        """Get winner of the game."""
        return self.get_final_state().get_winner()
    
    def get_margin_of_victory(self) -> Optional[int]:
        """Get margin of victory (100 - loser_final_position)."""
        final_state = self.get_final_state()
        loser_pos = final_state.get_loser_final_position()
        if loser_pos is None:
            return None
        return 100 - loser_pos
    
    def print_summary(self) -> None:
        """Print game summary."""
        final_state = self.get_final_state()
        winner = final_state.get_winner()
        margin = self.get_margin_of_victory()
        
        print("╔═══════════════════════════════════════════════════╗")
        print("║              GAME SUMMARY                         ║")
        print("╠═══════════════════════════════════════════════════╣")
        print(f"║  Total Moves: {len(self.moves):<35} ║")
        
        if winner:
            print(f"║  Winner: {winner}{' ' * (41 if winner == Player.A else 40)}║")
            print(f"║  Margin of Victory: {margin:<29} ║")
        else:
            print(f"║  Status: Game In Progress{' ' * 23}║")
        
        print("╠═══════════════════════════════════════════════════╣")
        print(f"║  Final Player A Position: {final_state.a_position:<23} ║")
        print(f"║  Final Player B Position: {final_state.b_position:<23} ║")
        print("╚═══════════════════════════════════════════════════╝")
    
    def print_move_history(self, start: int = 0, end: Optional[int] = None) -> None:
        """Print move history from start to end (inclusive)."""
        if end is None:
            end = len(self.moves)
        
        print(f"\n{'='*70}")
        print(f"{'MOVE HISTORY':^70}")
        print(f"{'='*70}\n")
        
        for i, move in enumerate(self.moves[start:end], start=start+1):
            print(f"Move {i:3d}: {move}")
    
    def print_full_replay(self) -> None:
        """Print complete game replay with all details."""
        print("\n" + "="*70)
        print(f"{'COMPLETE GAME REPLAY':^70}")
        print("="*70 + "\n")
        
        # Initial state
        print("INITIAL STATE:")
        self.initial_state.pretty_print()
        print()
        
        # All moves
        for i, move in enumerate(self.moves, 1):
            print(f"\n{'-'*70}")
            print(f"MOVE {i}")
            print(f"{'-'*70}")
            print(str(move))
            print()
            move.final_state.pretty_print()
        
        # Summary
        print("\n" + "="*70)
        self.print_summary()
        print("="*70 + "\n")
    
    def to_compact_string(self) -> str:
        """Generate compact string representation of game."""
        lines = [f"Game: {len(self.moves)} moves"]
        for i, move in enumerate(self.moves, 1):
            lines.append(f"{i:3d}. {move}")
        return "\n".join(lines)
    
    def get_statistics(self) -> dict:
        """Get game statistics."""
        stats = {
            'total_moves': len(self.moves),
            'winner': self.get_winner(),
            'margin_of_victory': self.get_margin_of_victory(),
            'player_a_final_pos': self.get_final_state().a_position,
            'player_b_final_pos': self.get_final_state().b_position,
            'captures_by_a': 0,
            'captures_by_b': 0,
            'ladders_hit': 0,
            'snakes_hit': 0,
            'scorpions_hit': 0,
            'grapes_hit': 0,
            'illegal_moves': 0,
            'skips': 0,
        }
        
        for move in self.moves:
            player = move.initial_state.current_player
            
            if move.capture_occurred:
                if player == Player.A:
                    stats['captures_by_a'] += 1
                else:
                    stats['captures_by_b'] += 1
            
            if move.ladder_triggered:
                stats['ladders_hit'] += 1
            if move.snake_triggered:
                stats['snakes_hit'] += 1
            if move.scorpion_triggered:
                stats['scorpions_hit'] += 1
            if move.grapes_triggered:
                stats['grapes_hit'] += 1
            if move.was_illegal:
                stats['illegal_moves'] += 1
            if move.action == Action.SKIP:
                stats['skips'] += 1
        
        return stats


def simulate_game(
    engine: 'GameEngine',
    dice_sequence: List[Tuple[int, int]],
    action_sequence: List[Action],
    verbose: bool = False
) -> GameReplay:
    """
    Simulate a complete game given dice and action sequences.
    
    Args:
        engine: Game engine to use
        dice_sequence: List of (dice1, dice2) tuples
        action_sequence: List of actions corresponding to each dice roll
        verbose: If True, print progress
    
    Returns:
        GameReplay object with complete history
    """
    if len(dice_sequence) != len(action_sequence):
        raise ValueError("Dice and action sequences must have same length")
    
    state = GameState.initial_state(board=engine.board)
    replay = GameReplay(initial_state=state, board=engine.board)
    
    for i, ((d1, d2), action) in enumerate(zip(dice_sequence, action_sequence)):
        if state.is_terminal():
            if verbose:
                print(f"Game ended at move {i}")
            break
        
        try:
            state, move_info = engine.execute_move(state, d1, d2, action)
            replay.add_move(move_info)
            
            if verbose:
                print(f"Move {i+1}: {move_info}")
        
        except ValueError as e:
            if verbose:
                print(f"Error at move {i+1}: {e}")
            raise
    
    return replay

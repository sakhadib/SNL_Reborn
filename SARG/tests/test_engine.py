"""
Comprehensive tests for SARG game engine.
Tests all components with edge cases.
"""

import pytest
import tempfile
from pathlib import Path

from src.engine import (
    Player, Action, SquareType,
    Board, CANONICAL_BOARD,
    GameState, GameEngine, GameReplay
)
from src.storage import GameStorage, GameWriter, GameReader, Move


class TestBoard:
    """Test board configuration and validation."""
    
    def test_board_initialization(self):
        """Test board initializes correctly."""
        board = Board()
        assert board.VERSION == "1.0"
        assert len(board.SAFE_ZONES) == 5
        assert len(board.LADDERS) == 7
        assert len(board.SNAKES) == 8
        assert len(board.SCORPIONS) == 6
        assert len(board.GRAPES) == 4
    
    def test_safe_zones(self):
        """Test safe zone positions."""
        board = Board()
        assert board.is_safe_zone(0)
        assert board.is_safe_zone(18)
        assert board.is_safe_zone(41)
        assert board.is_safe_zone(63)
        assert board.is_safe_zone(86)
        assert not board.is_safe_zone(50)
    
    def test_ladders(self):
        """Test ladder mappings."""
        board = Board()
        assert board.get_ladder_top(4) == 14
        assert board.get_ladder_top(71) == 83
        assert board.get_ladder_top(50) is None
    
    def test_snakes(self):
        """Test snake mappings."""
        board = Board()
        assert board.get_snake_tail(22) == 11
        assert board.get_snake_tail(97) == 72
        assert board.get_snake_tail(50) is None
    
    def test_previous_safe_zone(self):
        """Test demotion safe zone calculation."""
        board = Board()
        assert board.get_previous_safe_zone(0) == 0
        assert board.get_previous_safe_zone(20) == 18
        assert board.get_previous_safe_zone(50) == 41
        assert board.get_previous_safe_zone(100) == 86
    
    def test_mutual_exclusivity(self):
        """Test that all special squares are mutually exclusive."""
        board = Board()
        
        # Count all special positions
        all_positions = set()
        all_positions.update(board.SAFE_ZONES)
        all_positions.update([base for base, _ in board.LADDERS])
        all_positions.update([top for _, top in board.LADDERS])
        all_positions.update([head for head, _ in board.SNAKES])
        all_positions.update([tail for _, tail in board.SNAKES])
        all_positions.update(board.SCORPIONS)
        all_positions.update(board.GRAPES)
        
        # Total count should equal unique positions
        total_count = (
            len(board.SAFE_ZONES) +
            len(board.LADDERS) * 2 +
            len(board.SNAKES) * 2 +
            len(board.SCORPIONS) +
            len(board.GRAPES)
        )
        
        assert len(all_positions) == total_count, "Square types are not mutually exclusive"


class TestGameState:
    """Test game state representation and validation."""
    
    def test_initial_state(self):
        """Test initial game state."""
        state = GameState.initial_state()
        assert state.a_position == 0
        assert state.b_position == 0
        assert state.a_stun == 0
        assert state.b_stun == 0
        assert state.a_immunity == 0
        assert state.b_immunity == 0
        assert state.current_player == Player.A
        assert not state.is_terminal()
    
    def test_state_validation(self):
        """Test state validation catches invalid states."""
        with pytest.raises(AssertionError):
            GameState(
                a_position=101,  # Invalid
                a_stun=0, a_immunity=0,
                b_position=0, b_stun=0, b_immunity=0,
                current_player=Player.A
            )
        
        with pytest.raises(AssertionError):
            GameState(
                a_position=0, a_stun=4, a_immunity=0,  # Invalid stun
                b_position=0, b_stun=0, b_immunity=0,
                current_player=Player.A
            )
    
    def test_terminal_state(self):
        """Test terminal state detection."""
        state = GameState(
            a_position=100, a_stun=0, a_immunity=0,
            b_position=50, b_stun=0, b_immunity=0,
            current_player=Player.A
        )
        assert state.is_terminal()
        assert state.get_winner() == Player.A
        assert state.get_loser_final_position() == 50
    
    def test_immutable_update(self):
        """Test immutable state updates."""
        state1 = GameState.initial_state()
        state2 = state1.update(a_position=10)
        
        assert state1.a_position == 0  # Original unchanged
        assert state2.a_position == 10  # New state updated


class TestGameEngine:
    """Test game engine logic and transitions."""
    
    def setup_method(self):
        """Setup engine for each test."""
        self.engine = GameEngine()
    
    def test_basic_move(self):
        """Test basic movement."""
        state = GameState.initial_state()
        new_state, move_info = self.engine.execute_move(state, 3, 5, Action.CHOOSE_DIE_1)
        
        assert new_state.a_position == 3
        assert move_info.chosen_die == 3
        assert new_state.current_player == Player.B
    
    def test_ladder_effect(self):
        """Test ladder promotes player."""
        # Position player to land on ladder at position 4
        state = GameState(
            a_position=1, a_stun=0, a_immunity=0,
            b_position=0, b_stun=0, b_immunity=0,
            current_player=Player.A
        )
        
        new_state, move_info = self.engine.execute_move(state, 3, 5, Action.CHOOSE_DIE_1)
        
        # Should land on 4, ladder takes to 14
        assert new_state.a_position == 14
        assert move_info.ladder_triggered
    
    def test_snake_effect(self):
        """Test snake demotes player."""
        # Position player to land on snake at position 22
        state = GameState(
            a_position=20, a_stun=0, a_immunity=0,
            b_position=0, b_stun=0, b_immunity=0,
            current_player=Player.A
        )
        
        new_state, move_info = self.engine.execute_move(state, 2, 5, Action.CHOOSE_DIE_1)
        
        # Should land on 22, snake takes to 11
        assert new_state.a_position == 11
        assert move_info.snake_triggered
    
    def test_scorpion_stun(self):
        """Test scorpion applies stun."""
        # Position player to land on scorpion at position 6
        state = GameState(
            a_position=1, a_stun=0, a_immunity=0,
            b_position=0, b_stun=0, b_immunity=0,
            current_player=Player.A
        )
        
        new_state, move_info = self.engine.execute_move(state, 5, 3, Action.CHOOSE_DIE_1)
        
        assert new_state.a_position == 6
        assert new_state.a_stun == 3
        assert move_info.scorpion_triggered
    
    def test_grapes_immunity(self):
        """Test grapes grant immunity."""
        # Position player to land on grapes at position 39
        state = GameState(
            a_position=35, a_stun=0, a_immunity=0,
            b_position=0, b_stun=0, b_immunity=0,
            current_player=Player.A
        )
        
        new_state, move_info = self.engine.execute_move(state, 4, 2, Action.CHOOSE_DIE_1)
        
        assert new_state.a_position == 39
        assert new_state.a_immunity == 3
        assert move_info.grapes_triggered
    
    def test_immunity_blocks_snake(self):
        """Test immunity prevents snake effect."""
        # Position player with immunity to land on snake
        state = GameState(
            a_position=20, a_stun=0, a_immunity=2,
            b_position=0, b_stun=0, b_immunity=0,
            current_player=Player.A
        )
        
        new_state, move_info = self.engine.execute_move(state, 2, 5, Action.CHOOSE_DIE_1)
        
        # Should land on 22 but immunity prevents snake
        assert new_state.a_position == 22
        assert not move_info.snake_triggered
    
    def test_capture_demotion(self):
        """Test capture demotes opponent."""
        # Position B at 20, A moves to capture
        state = GameState(
            a_position=15, a_stun=0, a_immunity=0,
            b_position=20, b_stun=0, b_immunity=0,
            current_player=Player.A
        )
        
        new_state, move_info = self.engine.execute_move(state, 5, 3, Action.CHOOSE_DIE_1)
        
        assert new_state.a_position == 20
        assert new_state.b_position == 18  # Demoted to previous safe zone
        assert move_info.capture_occurred
    
    def test_capture_on_safe_zone(self):
        """Test capture does not demote on safe zone."""
        # Position B on safe zone 18
        state = GameState(
            a_position=13, a_stun=0, a_immunity=0,
            b_position=18, b_stun=0, b_immunity=0,
            current_player=Player.A
        )
        
        new_state, move_info = self.engine.execute_move(state, 5, 3, Action.CHOOSE_DIE_1)
        
        assert new_state.a_position == 18
        assert new_state.b_position == 18  # Not demoted
        assert not move_info.capture_occurred
    
    def test_stunned_player_skips(self):
        """Test stunned player automatically skips."""
        state = GameState(
            a_position=10, a_stun=2, a_immunity=0,
            b_position=0, b_stun=0, b_immunity=0,
            current_player=Player.A
        )
        
        new_state, move_info = self.engine.execute_move(state, 5, 3, Action.SKIP)
        
        assert new_state.a_position == 10  # Didn't move
        assert new_state.a_stun == 1  # Decreased
        assert move_info.was_stunned
    
    def test_illegal_move_overshoots(self):
        """Test illegal move that overshoots 100."""
        state = GameState(
            a_position=97, a_stun=0, a_immunity=0,
            b_position=0, b_stun=0, b_immunity=0,
            current_player=Player.A
        )
        
        new_state, move_info = self.engine.execute_move(state, 5, 3, Action.CHOOSE_DIE_1)
        
        assert new_state.a_position == 97  # Stays in place
        assert move_info.was_illegal
    
    def test_exact_win(self):
        """Test exact landing on 100 wins."""
        state = GameState(
            a_position=97, a_stun=0, a_immunity=0,
            b_position=0, b_stun=0, b_immunity=0,
            current_player=Player.A
        )
        
        new_state, move_info = self.engine.execute_move(state, 3, 5, Action.CHOOSE_DIE_1)
        
        assert new_state.a_position == 100
        assert new_state.is_terminal()
        assert new_state.get_winner() == Player.A
    
    def test_both_players_stunned(self):
        """Test both players stunned still alternates turns."""
        state = GameState(
            a_position=10, a_stun=2, a_immunity=0,
            b_position=5, b_stun=1, b_immunity=0,
            current_player=Player.A
        )
        
        # A's turn (stunned)
        state, _ = self.engine.execute_move(state, 5, 3, Action.SKIP)
        assert state.current_player == Player.B
        assert state.a_stun == 1
        
        # B's turn (stunned)
        state, _ = self.engine.execute_move(state, 2, 4, Action.SKIP)
        assert state.current_player == Player.A
        assert state.b_stun == 0


class TestBinaryStorage:
    """Test binary storage format."""
    
    def test_move_encoding(self):
        """Test move encoding and decoding."""
        move = Move(dice1=6, dice2=1, action=0)
        data = move.to_bytes()
        
        assert len(data) == 2
        decoded = Move.from_bytes(data)
        assert decoded.dice1 == 6
        assert decoded.dice2 == 1
        assert decoded.action == 0
    
    def test_move_encoding_all_values(self):
        """Test all dice and action combinations."""
        for d1 in range(1, 7):
            for d2 in range(1, 7):
                for action in range(3):
                    move = Move(dice1=d1, dice2=d2, action=action)
                    data = move.to_bytes()
                    decoded = Move.from_bytes(data)
                    
                    assert decoded.dice1 == d1
                    assert decoded.dice2 == d2
                    assert decoded.action == action
    
    def test_game_storage_write_read(self):
        """Test writing and reading games."""
        with tempfile.NamedTemporaryFile(delete=False, suffix='.sarg') as f:
            filepath = Path(f.name)
        
        try:
            # Simulate simple game
            engine = GameEngine()
            state = GameState.initial_state()
            replay = GameReplay(initial_state=state)
            
            # Make a few moves
            for d1, d2, action in [(3, 5, Action.CHOOSE_DIE_1), (2, 4, Action.CHOOSE_DIE_2)]:
                state, move_info = engine.execute_move(state, d1, d2, action)
                replay.add_move(move_info)
                if state.is_terminal():
                    break
            
            # Continue until win (simplified - just set winning position)
            state = state.update(a_position=100)
            replay.moves[-1].final_state = state
            
            # Write game
            writer = GameWriter(filepath)
            offset = writer.write_game(replay)
            
            assert offset >= 0
            
            # Read game back
            reader = GameReader(filepath, engine)
            loaded_replay = reader.read_game(offset)
            
            assert loaded_replay.get_move_count() == replay.get_move_count()
        
        finally:
            filepath.unlink()


if __name__ == '__main__':
    pytest.main([__file__, '-v'])

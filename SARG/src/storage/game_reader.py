"""
Game Reader - High-level interface for reading and replaying games from storage.
"""

from pathlib import Path
from typing import Optional
from ..engine import GameEngine, GameState, GameReplay, Action, Player
from .game_storage import GameStorage, GameRecord


class GameReader:
    """
    High-level reader for loading and replaying stored games.
    Converts binary format back to GameReplay.
    """
    
    def __init__(self, filepath: Path, engine: Optional[GameEngine] = None):
        """Initialize reader with storage file and game engine."""
        self.storage = GameStorage(filepath)
        self.engine = engine or GameEngine()
    
    def read_game(self, offset: int) -> GameReplay:
        """
        Read game at offset and reconstruct GameReplay.
        """
        # Read game record
        record = self.storage.read_game_at_offset(offset)
        
        # Reconstruct game by replaying moves
        return self._reconstruct_replay(record)
    
    def read_all_games(self) -> list:
        """Read all games and return list of GameReplay objects."""
        replays = []
        
        for record in self.storage.iter_games():
            replay = self._reconstruct_replay(record)
            replays.append(replay)
        
        return replays
    
    def _reconstruct_replay(self, record: GameRecord) -> GameReplay:
        """
        Reconstruct GameReplay from GameRecord by replaying all moves.
        Validates deterministic replay.
        """
        # Initialize game
        state = GameState.initial_state(board=self.engine.board)
        replay = GameReplay(initial_state=state, board=self.engine.board)
        
        # Replay all moves
        for move_data in record.moves:
            # Convert action int to enum
            action = Action(move_data.action)
            
            # Execute move
            state, move_info = self.engine.execute_move(
                state,
                move_data.dice1,
                move_data.dice2,
                action
            )
            
            replay.add_move(move_info)
        
        # Validate winner matches
        expected_winner = Player(record.header.winner)
        actual_winner = replay.get_winner()
        
        if actual_winner != expected_winner:
            raise ValueError(
                f"Replay validation failed: expected {expected_winner}, "
                f"got {actual_winner}"
            )
        
        return replay
    
    def validate_file(self) -> dict:
        """
        Validate entire file by replaying all games.
        Returns validation statistics.
        """
        stats = {
            'total_games': 0,
            'valid_games': 0,
            'invalid_games': 0,
            'errors': []
        }
        
        for i, record in enumerate(self.storage.iter_games()):
            stats['total_games'] += 1
            
            try:
                self._reconstruct_replay(record)
                stats['valid_games'] += 1
            except Exception as e:
                stats['invalid_games'] += 1
                stats['errors'].append((i, str(e)))
        
        return stats
    
    def get_game_metadata(self, offset: int) -> dict:
        """
        Get game metadata without full replay.
        Faster than full reconstruction.
        """
        record = self.storage.read_game_at_offset(offset)
        
        return {
            'player_a_id': record.header.player_a_id,
            'player_b_id': record.header.player_b_id,
            'winner': Player(record.header.winner),
            'move_count': record.header.move_count,
            'size_bytes': record.get_size()
        }
    
    def count_games(self) -> int:
        """Count total games in file."""
        return self.storage.count_games()
    
    def get_file_stats(self) -> dict:
        """Get file-level statistics."""
        return {
            'file_size_bytes': self.storage.get_file_size(),
            'total_games': self.count_games(),
            'file_header': self.storage.read_file_header()
        }

"""
Game Writer - High-level interface for writing games to storage.
"""

from pathlib import Path
from typing import Optional
from ..engine import GameReplay, Player
from .game_storage import GameStorage, GameRecord, GameHeader, Move


class GameWriter:
    """
    High-level writer for storing games.
    Converts GameReplay to binary format.
    """
    
    def __init__(self, filepath: Path):
        """Initialize writer with storage file."""
        self.storage = GameStorage(filepath)
    
    def write_game(
        self,
        replay: GameReplay,
        player_a_id: int = 0,
        player_b_id: int = 1
    ) -> int:
        """
        Write game replay to storage.
        Returns byte offset where game was written.
        """
        # Get winner
        winner_player = replay.get_winner()
        if winner_player is None:
            raise ValueError("Cannot store incomplete game")
        
        winner = 0 if winner_player == Player.A else 1
        
        # Create game header
        header = GameHeader(
            player_a_id=player_a_id,
            player_b_id=player_b_id,
            winner=winner,
            move_count=len(replay.moves)
        )
        
        # Create moves
        moves = []
        for move_info in replay.moves:
            from ..engine import Action
            
            move = Move(
                dice1=move_info.dice1,
                dice2=move_info.dice2,
                action=move_info.action.value  # Convert enum to int
            )
            moves.append(move)
        
        # Create game record
        record = GameRecord(header=header, moves=moves)
        
        # Write to storage
        return self.storage.append_game(record)
    
    def write_games_batch(
        self,
        replays: list,
        player_ids: Optional[list] = None
    ) -> list:
        """
        Write multiple games in batch.
        Returns list of byte offsets.
        """
        offsets = []
        
        for i, replay in enumerate(replays):
            if player_ids and i < len(player_ids):
                a_id, b_id = player_ids[i]
            else:
                a_id, b_id = 0, 1
            
            offset = self.write_game(replay, a_id, b_id)
            offsets.append(offset)
        
        return offsets

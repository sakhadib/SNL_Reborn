"""
Rating Tracker - Persistent storage and management of agent ratings.

Maintains global Elo ratings across multiple tournaments with:
- JSON-based persistent storage
- Rating history tracking
- Tournament-to-tournament carryover
"""

import json
from pathlib import Path
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict
from datetime import datetime


@dataclass
class RatingEntry:
    """Single rating entry for an agent."""
    agent_id: str
    rating: float
    games_played: int
    wins: int
    losses: int
    total_margin: int
    last_updated: str
    
    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: dict) -> 'RatingEntry':
        """Create from dictionary."""
        return cls(**data)


class RatingTracker:
    """
    Manages persistent Elo ratings across tournaments.
    
    Features:
    - Load/save ratings from JSON
    - Initialize new agents at 1500
    - Track rating history
    - Preserve ratings between tournaments
    """
    
    INITIAL_RATING = 1500.0
    
    def __init__(self, rating_file: Path):
        """
        Initialize rating tracker.
        
        Args:
            rating_file: Path to JSON file storing ratings
        """
        self.rating_file = rating_file
        self.ratings: Dict[str, RatingEntry] = {}
        self.rating_history: List[Dict[str, float]] = []
        
        # Load existing ratings if file exists
        if rating_file.exists():
            self.load()
    
    def get_rating(self, agent_id: str) -> float:
        """
        Get current rating for an agent.
        
        Args:
            agent_id: Agent identifier
            
        Returns:
            Current Elo rating (1500 if new agent)
        """
        if agent_id not in self.ratings:
            self._initialize_agent(agent_id)
        return self.ratings[agent_id].rating
    
    def get_all_ratings(self) -> Dict[str, float]:
        """Get all current ratings as dict."""
        return {agent_id: entry.rating for agent_id, entry in self.ratings.items()}
    
    def update_rating(
        self,
        agent_id: str,
        new_rating: float,
        won: bool,
        margin: int
    ):
        """
        Update rating after a game.
        
        Args:
            agent_id: Agent identifier
            new_rating: New rating after update
            won: Whether agent won
            margin: Margin of victory (positive for winner, negative for loser)
        """
        if agent_id not in self.ratings:
            self._initialize_agent(agent_id)
        
        entry = self.ratings[agent_id]
        entry.rating = new_rating
        entry.games_played += 1
        if won:
            entry.wins += 1
            entry.total_margin += margin
        else:
            entry.losses += 1
            entry.total_margin -= margin
        entry.last_updated = datetime.now().isoformat()
    
    def snapshot_ratings(self):
        """Save current ratings to history."""
        self.rating_history.append(self.get_all_ratings().copy())
    
    def _initialize_agent(self, agent_id: str):
        """Initialize new agent with default rating."""
        self.ratings[agent_id] = RatingEntry(
            agent_id=agent_id,
            rating=self.INITIAL_RATING,
            games_played=0,
            wins=0,
            losses=0,
            total_margin=0,
            last_updated=datetime.now().isoformat()
        )
    
    def save(self):
        """Save ratings to JSON file."""
        data = {
            'version': '1.0',
            'last_updated': datetime.now().isoformat(),
            'ratings': {
                agent_id: entry.to_dict() 
                for agent_id, entry in self.ratings.items()
            },
            'history_length': len(self.rating_history)
        }
        
        self.rating_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.rating_file, 'w') as f:
            json.dump(data, f, indent=2)
    
    def load(self):
        """Load ratings from JSON file."""
        with open(self.rating_file, 'r') as f:
            data = json.load(f)
        
        self.ratings = {
            agent_id: RatingEntry.from_dict(entry_data)
            for agent_id, entry_data in data['ratings'].items()
        }
    
    def get_leaderboard(self, min_games: int = 0) -> List[tuple]:
        """
        Get sorted leaderboard.
        
        Args:
            min_games: Minimum games to be included
            
        Returns:
            List of (agent_id, rating, games, wins, losses, win_rate)
        """
        leaderboard = []
        for agent_id, entry in self.ratings.items():
            if entry.games_played >= min_games:
                win_rate = entry.wins / entry.games_played if entry.games_played > 0 else 0.0
                leaderboard.append((
                    agent_id,
                    entry.rating,
                    entry.games_played,
                    entry.wins,
                    entry.losses,
                    win_rate
                ))
        
        # Sort by rating descending
        leaderboard.sort(key=lambda x: x[1], reverse=True)
        return leaderboard
    
    def get_stats(self, agent_id: str) -> Optional[RatingEntry]:
        """Get detailed stats for an agent."""
        return self.ratings.get(agent_id)
    
    def reset_agent(self, agent_id: str):
        """Reset agent to initial rating."""
        if agent_id in self.ratings:
            self._initialize_agent(agent_id)
    
    def reset_all(self):
        """Reset all agents to initial ratings."""
        for agent_id in list(self.ratings.keys()):
            self._initialize_agent(agent_id)

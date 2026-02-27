"""
Tournament Statistics - Collect and report tournament metrics.
"""

from dataclasses import dataclass, field
from typing import Dict, List
from collections import defaultdict


@dataclass
class MatchupStats:
    """Statistics for a specific agent matchup."""
    agent_a: str
    agent_b: str
    a_wins: int = 0
    b_wins: int = 0
    a_total_margin: int = 0
    b_total_margin: int = 0
    total_turns: int = 0
    games_played: int = 0
    
    def win_rate_a(self) -> float:
        """Win rate for agent A."""
        return self.a_wins / self.games_played if self.games_played > 0 else 0.0
    
    def win_rate_b(self) -> float:
        """Win rate for agent B."""
        return self.b_wins / self.games_played if self.games_played > 0 else 0.0
    
    def avg_margin_a(self) -> float:
        """Average victory margin for agent A."""
        return self.a_total_margin / self.a_wins if self.a_wins > 0 else 0.0
    
    def avg_margin_b(self) -> float:
        """Average victory margin for agent B."""
        return self.b_total_margin / self.b_wins if self.b_wins > 0 else 0.0
    
    def avg_turns(self) -> float:
        """Average game length in turns."""
        return self.total_turns / self.games_played if self.games_played > 0 else 0.0


class TournamentStats:
    """
    Collect and analyze tournament statistics.
    
    Tracks:
    - Head-to-head matchup results
    - Margin distributions
    - Win rates
    - Rating changes
    """
    
    def __init__(self):
        """Initialize statistics collector."""
        self.matchups: Dict[tuple, MatchupStats] = {}
        self.agent_games: Dict[str, int] = defaultdict(int)
        self.agent_wins: Dict[str, int] = defaultdict(int)
        self.agent_margins: Dict[str, List[int]] = defaultdict(list)
        self.rating_history: List[Dict[str, float]] = []
    
    def record_game(
        self,
        agent_a: str,
        agent_b: str,
        winner: str,
        margin: int,
        turns: int
    ):
        """
        Record a game result.
        
        Args:
            agent_a: First agent ID
            agent_b: Second agent ID
            winner: Winner agent ID
            margin: Margin of victory
            turns: Number of turns
        """
        # Normalize matchup key (alphabetical order)
        key = tuple(sorted([agent_a, agent_b]))
        
        if key not in self.matchups:
            self.matchups[key] = MatchupStats(agent_a=key[0], agent_b=key[1])
        
        matchup = self.matchups[key]
        matchup.games_played += 1
        matchup.total_turns += turns
        
        # Record winner
        if winner == agent_a:
            if key[0] == agent_a:
                matchup.a_wins += 1
                matchup.a_total_margin += margin
            else:
                matchup.b_wins += 1
                matchup.b_total_margin += margin
        else:
            if key[0] == agent_b:
                matchup.a_wins += 1
                matchup.a_total_margin += margin
            else:
                matchup.b_wins += 1
                matchup.b_total_margin += margin
        
        # Record agent-level stats
        self.agent_games[agent_a] += 1
        self.agent_games[agent_b] += 1
        self.agent_wins[winner] += 1
        self.agent_margins[winner].append(margin)
    
    def get_matchup(self, agent_a: str, agent_b: str) -> MatchupStats:
        """Get statistics for a specific matchup."""
        key = tuple(sorted([agent_a, agent_b]))
        return self.matchups.get(key)
    
    def get_head_to_head(self, agent_a: str, agent_b: str) -> Dict:
        """Get head-to-head statistics between two agents."""
        matchup = self.get_matchup(agent_a, agent_b)
        if not matchup:
            return None
        
        # Determine which position each agent is in
        if matchup.agent_a == agent_a:
            return {
                'agent': agent_a,
                'opponent': agent_b,
                'wins': matchup.a_wins,
                'losses': matchup.b_wins,
                'win_rate': matchup.win_rate_a(),
                'avg_margin': matchup.avg_margin_a(),
                'games': matchup.games_played
            }
        else:
            return {
                'agent': agent_a,
                'opponent': agent_b,
                'wins': matchup.b_wins,
                'losses': matchup.a_wins,
                'win_rate': matchup.win_rate_b(),
                'avg_margin': matchup.avg_margin_b(),
                'games': matchup.games_played
            }
    
    def get_agent_summary(self, agent_id: str) -> Dict:
        """Get summary statistics for an agent."""
        games = self.agent_games.get(agent_id, 0)
        wins = self.agent_wins.get(agent_id, 0)
        losses = games - wins
        margins = self.agent_margins.get(agent_id, [])
        
        return {
            'agent': agent_id,
            'games': games,
            'wins': wins,
            'losses': losses,
            'win_rate': wins / games if games > 0 else 0.0,
            'avg_margin': sum(margins) / len(margins) if margins else 0.0,
            'max_margin': max(margins) if margins else 0,
            'min_margin': min(margins) if margins else 0
        }
    
    def get_all_matchups(self) -> List[MatchupStats]:
        """Get all matchup statistics."""
        return list(self.matchups.values())
    
    def snapshot_ratings(self, ratings: Dict[str, float]):
        """Save rating snapshot."""
        self.rating_history.append(ratings.copy())
    
    def print_summary(self):
        """Print tournament summary."""
        print("\n" + "="*70)
        print("TOURNAMENT SUMMARY")
        print("="*70)
        
        total_games = sum(m.games_played for m in self.matchups.values())
        print(f"\nTotal Games: {total_games}")
        print(f"Total Matchups: {len(self.matchups)}")
        
        print("\n" + "-"*70)
        print("AGENT PERFORMANCE")
        print("-"*70)
        
        agents = sorted(self.agent_games.keys())
        for agent in agents:
            stats = self.get_agent_summary(agent)
            print(f"\n{agent}:")
            print(f"  Games: {stats['games']}")
            print(f"  Win Rate: {stats['win_rate']:.1%}")
            print(f"  Avg Margin: {stats['avg_margin']:.1f}")

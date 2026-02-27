"""
Margin-Scaled Elo Rating System for SARG.

Implements the evaluation mechanism from Evaluation_And_Scoring_Mechanism.md:
- Base Elo with K=24
- Margin multiplier: M = 1 + alpha * D_rel
- D_rel = (100 - loser_final_position) / 100
- Recommended alpha = 0.75
"""

from dataclasses import dataclass
from typing import Tuple
import math


@dataclass
class GameResult:
    """Result of a single game for rating calculation."""
    winner_id: str
    loser_id: str
    loser_final_position: int
    num_turns: int
    
    def get_margin(self) -> int:
        """Calculate margin of victory D = 100 - L_final."""
        return 100 - self.loser_final_position
    
    def get_relative_margin(self) -> float:
        """Calculate relative margin D_rel = D / 100."""
        return self.get_margin() / 100.0


class EloRating:
    """
    Margin-scaled Elo rating system.
    
    Implements zero-sum rating updates with margin-of-victory scaling.
    """
    
    def __init__(self, k_factor: float = 24.0, alpha: float = 0.75):
        """
        Initialize Elo rating system.
        
        Args:
            k_factor: Base K-factor for rating updates (default: 24)
            alpha: Margin sensitivity parameter (default: 0.75)
                  M = 1 + alpha * D_rel, so M in [1, 1+alpha]
        """
        self.k_factor = k_factor
        self.alpha = alpha
    
    def expected_score(self, rating_a: float, rating_b: float) -> float:
        """
        Calculate expected score for player A.
        
        E_A = 1 / (1 + 10^((R_B - R_A)/400))
        
        Args:
            rating_a: Current rating of player A
            rating_b: Current rating of player B
            
        Returns:
            Expected score for player A (between 0 and 1)
        """
        return 1.0 / (1.0 + math.pow(10, (rating_b - rating_a) / 400.0))
    
    def margin_multiplier(self, result: GameResult) -> float:
        """
        Calculate margin multiplier M = 1 + alpha * D_rel.
        
        Args:
            result: Game result with margin information
            
        Returns:
            Margin multiplier in range [1, 1 + alpha]
        """
        d_rel = result.get_relative_margin()
        return 1.0 + self.alpha * d_rel
    
    def update_ratings(
        self,
        winner_rating: float,
        loser_rating: float,
        result: GameResult
    ) -> Tuple[float, float]:
        """
        Update ratings after a game using margin-scaled Elo.
        
        R'_winner = R_winner + K * M * (1 - E_winner)
        R'_loser = R_loser + K * M * (0 - E_loser)
        
        Args:
            winner_rating: Current rating of winner
            loser_rating: Current rating of loser
            result: Game result with margin information
            
        Returns:
            Tuple of (new_winner_rating, new_loser_rating)
        """
        # Calculate expected scores
        expected_winner = self.expected_score(winner_rating, loser_rating)
        expected_loser = 1.0 - expected_winner
        
        # Calculate margin multiplier
        margin_mult = self.margin_multiplier(result)
        
        # Calculate rating changes
        winner_change = self.k_factor * margin_mult * (1.0 - expected_winner)
        loser_change = self.k_factor * margin_mult * (0.0 - expected_loser)
        
        # Apply updates (zero-sum property preserved)
        new_winner_rating = winner_rating + winner_change
        new_loser_rating = loser_rating + loser_change
        
        return new_winner_rating, new_loser_rating
    
    def rating_change(
        self,
        winner_rating: float,
        loser_rating: float,
        result: GameResult
    ) -> float:
        """
        Calculate rating change for winner (loser gets negative of this).
        
        Args:
            winner_rating: Current rating of winner
            loser_rating: Current rating of loser
            result: Game result with margin information
            
        Returns:
            Rating points gained by winner (lost by loser)
        """
        expected_winner = self.expected_score(winner_rating, loser_rating)
        margin_mult = self.margin_multiplier(result)
        return self.k_factor * margin_mult * (1.0 - expected_winner)
    
    def max_rating_swing(self) -> float:
        """
        Calculate maximum possible rating swing in one game.
        
        Occurs when:
        - Lower-rated player wins
        - Margin is maximum (D_rel = 1.0)
        
        Returns:
            Maximum rating change for winner
        """
        return self.k_factor * (1.0 + self.alpha)

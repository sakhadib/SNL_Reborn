"""
Base Agent class and helper functions for querying game state.
"""

from abc import ABC, abstractmethod
from typing import Optional, Tuple
from ..engine import GameState, GameEngine, Action, Player, CANONICAL_BOARD
from ..engine.enums import WINNING_POSITION


class AgentHelper:
    """
    Helper functions for agents to query game state and evaluate moves.
    Provides the helper functions mentioned in agents.md specification.
    """
    
    def __init__(self, engine: GameEngine, state: GameState, player: Player, dice1: int, dice2: int):
        """Initialize helper with current game context."""
        self.engine = engine
        self.state = state
        self.player = player
        self.opponent = player.opponent()
        self.dice1 = dice1
        self.dice2 = dice2
        self.board = engine.board
        self.current_pos = state.get_player_position(player)
        self.opponent_pos = state.get_player_position(self.opponent)
    
    def legal(self, die_value: int) -> bool:
        """Check if using this die value is legal."""
        action = Action.CHOOSE_DIE_1 if die_value == self.dice1 else Action.CHOOSE_DIE_2
        is_valid, _ = self.engine.validate_action(self.state, self.dice1, self.dice2, action)
        
        # Also check if it overshoots
        if is_valid and self.current_pos + die_value > WINNING_POSITION:
            return False
        
        return is_valid
    
    def landing(self, die_value: int) -> int:
        """Get landing position (before any square effects)."""
        return self.current_pos + die_value
    
    def final_pos(self, die_value: int) -> int:
        """Get final position after snake/ladder/scorpion/grapes but before capture."""
        landing = self.landing(die_value)
        
        # Apply ladder
        if self.board.is_ladder(landing):
            return self.board.get_ladder_top(landing)
        
        # Apply snake (if not immune)
        if self.board.is_snake(landing):
            if not self.state.is_player_immune(self.player):
                return self.board.get_snake_tail(landing)
        
        return landing
    
    def is_snake(self, die_value: int) -> bool:
        """Check if landing on this die leads to snake."""
        landing = self.landing(die_value)
        return self.board.is_snake(landing)
    
    def is_scorpion(self, die_value: int) -> bool:
        """Check if landing on this die leads to scorpion."""
        landing = self.landing(die_value)
        return self.board.is_scorpion(landing)
    
    def is_grape(self, die_value: int) -> bool:
        """Check if landing on this die leads to grapes."""
        landing = self.landing(die_value)
        return self.board.is_grapes(landing)
    
    def is_safe(self, die_value: int) -> bool:
        """Check if final position is a safe zone."""
        final = self.final_pos(die_value)
        return self.board.is_safe_zone(final)
    
    def captures(self, die_value: int) -> bool:
        """Check if this move captures opponent."""
        final = self.final_pos(die_value)
        return final == self.opponent_pos and not self.board.is_safe_zone(self.opponent_pos)
    
    def opponent_can_capture(self, position: int) -> bool:
        """
        Check if opponent can capture us if we're at this position.
        Simple one-step lookahead.
        """
        # Check all possible opponent moves (1-6)
        for opp_die in range(1, 7):
            opp_landing = self.opponent_pos + opp_die
            
            if opp_landing > WINNING_POSITION:
                continue
            
            # Check final position after ladder/snake
            opp_final = opp_landing
            if self.board.is_ladder(opp_landing):
                opp_final = self.board.get_ladder_top(opp_landing)
            elif self.board.is_snake(opp_landing):
                # Assume opponent not immune (conservative)
                opp_final = self.board.get_snake_tail(opp_landing)
            
            if opp_final == position and not self.board.is_safe_zone(position):
                return True
        
        return False
    
    def progress(self, die_value: int) -> int:
        """Get progress made by this move."""
        return self.final_pos(die_value) - self.current_pos
    
    def ladder_gain(self, die_value: int) -> int:
        """Get ladder gain (0 if no ladder)."""
        landing = self.landing(die_value)
        if self.board.is_ladder(landing):
            top = self.board.get_ladder_top(landing)
            return top - landing
        return 0
    
    def snake_loss(self, die_value: int) -> int:
        """Get snake loss (0 if no snake or immune)."""
        landing = self.landing(die_value)
        if self.board.is_snake(landing) and not self.state.is_player_immune(self.player):
            tail = self.board.get_snake_tail(landing)
            return landing - tail
        return 0
    
    def scorpion_penalty(self, die_value: int) -> int:
        """Return 1 if scorpion, 0 otherwise."""
        return 1 if self.is_scorpion(die_value) and not self.state.is_player_immune(self.player) else 0
    
    def grape_bonus(self, die_value: int) -> int:
        """Return 1 if grapes, 0 otherwise."""
        return 1 if self.is_grape(die_value) else 0
    
    def capture_bonus(self, die_value: int) -> int:
        """Return 1 if captures opponent, 0 otherwise."""
        return 1 if self.captures(die_value) else 0
    
    def exposure_penalty(self, die_value: int) -> int:
        """Return 1 if opponent can capture, 0 otherwise."""
        final = self.final_pos(die_value)
        return 1 if self.opponent_can_capture(final) else 0


class BaseAgent(ABC):
    """
    Base class for all agents.
    """
    
    def __init__(self, name: str):
        """Initialize agent with a name."""
        self.name = name
    
    @abstractmethod
    def choose_action(
        self,
        engine: GameEngine,
        state: GameState,
        player: Player,
        dice1: int,
        dice2: int
    ) -> Action:
        """
        Choose action given game state and dice roll.
        
        Args:
            engine: Game engine
            state: Current game state
            player: Which player this agent is
            dice1: First die value
            dice2: Second die value
        
        Returns:
            Action to take
        """
        pass
    
    def __str__(self) -> str:
        return self.name
    
    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(name='{self.name}')"

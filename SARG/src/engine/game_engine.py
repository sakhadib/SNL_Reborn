"""
Game Engine - Complete FSM implementation with full validation.
Implements the deterministic state machine for SARG.
"""

from typing import List, Tuple, Optional
from dataclasses import dataclass
from .enums import Player, Action, MIN_DICE, MAX_DICE, WINNING_POSITION
from .board import Board, CANONICAL_BOARD
from .game_state import GameState


@dataclass
class MoveInfo:
    """Information about a move and its consequences."""
    dice1: int
    dice2: int
    action: Action
    initial_state: GameState
    final_state: GameState
    
    # Move details
    was_stunned: bool
    chosen_die: Optional[int]
    landing_position: Optional[int]  # Before effects
    final_position: Optional[int]    # After effects
    
    # Effects triggered
    ladder_triggered: bool
    snake_triggered: bool
    scorpion_triggered: bool
    grapes_triggered: bool
    capture_occurred: bool
    demoted_from: Optional[int]
    demoted_to: Optional[int]
    
    # Validation
    was_illegal: bool
    illegal_reason: Optional[str]
    
    def __str__(self) -> str:
        """Human-readable move description."""
        player = self.initial_state.current_player
        
        if self.was_stunned:
            return f"{player} skipped turn (stunned)"
        
        if self.action == Action.SKIP:
            return f"{player} chose to skip (d1={self.dice1}, d2={self.dice2})"
        
        move_str = f"{player} rolled [{self.dice1}, {self.dice2}], chose {self.chosen_die}"
        
        if self.was_illegal:
            return f"{move_str} - ILLEGAL: {self.illegal_reason}"
        
        pos_change = f" moved {self.initial_state.get_player_position(player)} → {self.final_position}"
        
        effects = []
        if self.ladder_triggered:
            effects.append(f"ladder to {self.final_position}")
        if self.snake_triggered:
            effects.append(f"snake to {self.final_position}")
        if self.scorpion_triggered:
            effects.append("stunned for 3 turns")
        if self.grapes_triggered:
            effects.append("gained 3-turn immunity")
        if self.capture_occurred:
            effects.append(f"captured opponent ({self.demoted_from} → {self.demoted_to})")
        
        if effects:
            return f"{move_str}{pos_change} [{', '.join(effects)}]"
        
        return f"{move_str}{pos_change}"


class GameEngine:
    """
    SARG Game Engine - Deterministic FSM Implementation
    
    Implements complete transition function with full validation.
    """
    
    def __init__(self, board: Optional[Board] = None):
        """Initialize game engine with board configuration."""
        self.board = board or CANONICAL_BOARD
    
    def validate_action(
        self,
        state: GameState,
        dice1: int,
        dice2: int,
        action: Action
    ) -> Tuple[bool, Optional[str]]:
        """
        Validate if action is legal in current state.
        Returns (is_valid, error_message)
        """
        # Validate dice values
        if not (MIN_DICE <= dice1 <= MAX_DICE):
            return False, f"Invalid dice1: {dice1}"
        if not (MIN_DICE <= dice2 <= MAX_DICE):
            return False, f"Invalid dice2: {dice2}"
        
        # Validate action type
        if action not in [Action.CHOOSE_DIE_1, Action.CHOOSE_DIE_2, Action.SKIP]:
            return False, f"Invalid action: {action}"
        
        # Terminal state check
        if state.is_terminal():
            return False, "Game already ended"
        
        current_player = state.current_player
        current_pos = state.get_player_position(current_player)
        
        # If stunned, only forced skip allowed
        if state.is_player_stunned(current_player):
            if action != Action.SKIP:
                return False, "Player is stunned, must skip"
            return True, None
        
        # Check skip is always allowed when not stunned
        if action == Action.SKIP:
            return True, None
        
        # Check if chosen die is legal
        chosen_die = dice1 if action == Action.CHOOSE_DIE_1 else dice2
        new_pos = current_pos + chosen_die
        
        if new_pos > WINNING_POSITION:
            # This is allowed but becomes a forced stay
            return True, None
        
        return True, None
    
    def execute_move(
        self,
        state: GameState,
        dice1: int,
        dice2: int,
        action: Action
    ) -> Tuple[GameState, MoveInfo]:
        """
        Execute a move and return new state with move information.
        Implements complete FSM transition function.
        """
        # Validate action
        is_valid, error = self.validate_action(state, dice1, dice2, action)
        if not is_valid:
            raise ValueError(f"Invalid move: {error}")
        
        current_player = state.current_player
        opponent = current_player.opponent()
        
        # Initialize move info
        move_info = MoveInfo(
            dice1=dice1,
            dice2=dice2,
            action=action,
            initial_state=state,
            final_state=state,  # Will be updated
            was_stunned=state.is_player_stunned(current_player),
            chosen_die=None,
            landing_position=None,
            final_position=None,
            ladder_triggered=False,
            snake_triggered=False,
            scorpion_triggered=False,
            grapes_triggered=False,
            capture_occurred=False,
            demoted_from=None,
            demoted_to=None,
            was_illegal=False,
            illegal_reason=None
        )
        
        # Handle stunned player
        if state.is_player_stunned(current_player):
            new_state = self._handle_stunned_turn(state, current_player)
            move_info.final_state = new_state
            return new_state, move_info
        
        # Handle skip action
        if action == Action.SKIP:
            new_state = self._handle_skip(state, current_player)
            move_info.final_state = new_state
            return new_state, move_info
        
        # Execute chosen die move
        chosen_die = dice1 if action == Action.CHOOSE_DIE_1 else dice2
        move_info.chosen_die = chosen_die
        
        current_pos = state.get_player_position(current_player)
        landing_pos = current_pos + chosen_die
        move_info.landing_position = landing_pos
        
        # Check if move is illegal (overshoots 100)
        if landing_pos > WINNING_POSITION:
            move_info.was_illegal = True
            move_info.illegal_reason = f"Overshoots winning position ({landing_pos} > 100)"
            move_info.final_position = current_pos  # Stay in place
            new_state = self._end_turn(state, current_player)
            move_info.final_state = new_state
            return new_state, move_info
        
        # Apply square effects
        new_state, move_info = self._apply_square_effects(
            state, current_player, landing_pos, move_info
        )
        
        # Check for win condition
        if move_info.final_position == WINNING_POSITION:
            move_info.final_state = new_state
            return new_state, move_info
        
        # Apply capture rule
        new_state, move_info = self._apply_capture(new_state, current_player, move_info)
        
        # End turn (switch player, decay immunity)
        new_state = self._end_turn(new_state, current_player)
        
        move_info.final_state = new_state
        return new_state, move_info
    
    def _handle_stunned_turn(self, state: GameState, player: Player) -> GameState:
        """Handle turn when player is stunned."""
        # Decrease stun counter
        new_stun = state.get_player_stun(player) - 1
        
        # Decrease immunity counter if applicable
        new_immunity = max(0, state.get_player_immunity(player) - 1)
        
        # Update state
        if player == Player.A:
            return state.update(
                a_stun=new_stun,
                a_immunity=new_immunity,
                current_player=player.opponent()
            )
        else:
            return state.update(
                b_stun=new_stun,
                b_immunity=new_immunity,
                current_player=player.opponent()
            )
    
    def _handle_skip(self, state: GameState, player: Player) -> GameState:
        """Handle voluntary skip action."""
        # Just end turn
        return self._end_turn(state, player)
    
    def _apply_square_effects(
        self,
        state: GameState,
        player: Player,
        landing_pos: int,
        move_info: MoveInfo
    ) -> Tuple[GameState, MoveInfo]:
        """Apply square effects at landing position."""
        final_pos = landing_pos
        is_immune = state.is_player_immune(player)
        
        # All effects are checked at the LANDING position only
        # Squares are mutually exclusive, so we check them in priority order
        
        # 1. Check for ladder (highest priority movement)
        if self.board.is_ladder(landing_pos):
            ladder_top = self.board.get_ladder_top(landing_pos)
            final_pos = ladder_top
            move_info.ladder_triggered = True
        
        # 2. Check for snake (if not immune, second priority movement)
        elif self.board.is_snake(landing_pos):
            if not is_immune:
                snake_tail = self.board.get_snake_tail(landing_pos)
                final_pos = snake_tail
                move_info.snake_triggered = True
            # If immune, ignore snake
        
        # 3. Check for scorpion at LANDING position (if not immune)
        if self.board.is_scorpion(landing_pos):
            if not is_immune:
                # Apply stun
                if player == Player.A:
                    state = state.update(a_stun=3)
                else:
                    state = state.update(b_stun=3)
                move_info.scorpion_triggered = True
        
        # 4. Check for grapes at LANDING position
        if self.board.is_grapes(landing_pos):
            # Grant immunity
            if player == Player.A:
                state = state.update(a_immunity=3)
            else:
                state = state.update(b_immunity=3)
            move_info.grapes_triggered = True
        
        # Update position to final position (after ladder/snake movement)
        if player == Player.A:
            state = state.update(a_position=final_pos)
        else:
            state = state.update(b_position=final_pos)
        
        move_info.final_position = final_pos
        return state, move_info
    
    def _apply_capture(
        self,
        state: GameState,
        player: Player,
        move_info: MoveInfo
    ) -> Tuple[GameState, MoveInfo]:
        """Apply capture rule if applicable."""
        player_pos = state.get_player_position(player)
        opponent = player.opponent()
        opponent_pos = state.get_player_position(opponent)
        
        # Check if capture occurs
        if player_pos == opponent_pos:
            # Check if opponent is on safe zone
            if self.board.is_safe_zone(opponent_pos):
                # No demotion, both can stack
                move_info.capture_occurred = False
            else:
                # Demote opponent to previous safe zone
                demote_to = self.board.get_previous_safe_zone(opponent_pos)
                move_info.capture_occurred = True
                move_info.demoted_from = opponent_pos
                move_info.demoted_to = demote_to
                
                # Update opponent position
                if opponent == Player.A:
                    state = state.update(a_position=demote_to)
                else:
                    state = state.update(b_position=demote_to)
        
        return state, move_info
    
    def _end_turn(
        self,
        state: GameState,
        player: Player
    ) -> GameState:
        """End turn: decay immunity and switch player."""
        # Decay immunity counter
        new_immunity = max(0, state.get_player_immunity(player) - 1)
        
        # Switch player
        next_player = player.opponent()
        
        if player == Player.A:
            return state.update(
                a_immunity=new_immunity,
                current_player=next_player
            )
        else:
            return state.update(
                b_immunity=new_immunity,
                current_player=next_player
            )
    
    def get_legal_actions(
        self,
        state: GameState,
        dice1: int,
        dice2: int
    ) -> List[Action]:
        """Get list of legal actions for current state and dice."""
        legal_actions = []
        
        for action in [Action.CHOOSE_DIE_1, Action.CHOOSE_DIE_2, Action.SKIP]:
            is_valid, _ = self.validate_action(state, dice1, dice2, action)
            if is_valid:
                legal_actions.append(action)
        
        return legal_actions

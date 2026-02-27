"""
All 15 heuristic agents as per agents.md specification.
"""

from ..engine import GameEngine, GameState, Player, Action
from .base_agent import BaseAgent, AgentHelper


class MaximAgent(BaseAgent):
    """Pure forward greed - always choose larger die."""
    
    def __init__(self):
        super().__init__("MAXIM")
    
    def choose_action(self, engine, state, player, dice1, dice2):
        helper = AgentHelper(engine, state, player, dice1, dice2)
        
        if helper.legal(dice1) and helper.legal(dice2):
            return Action.CHOOSE_DIE_1 if dice1 > dice2 else Action.CHOOSE_DIE_2
        elif helper.legal(dice1):
            return Action.CHOOSE_DIE_1
        elif helper.legal(dice2):
            return Action.CHOOSE_DIE_2
        else:
            return Action.SKIP


class MinimAgent(BaseAgent):
    """Minimal forward exposure - always choose smaller die."""
    
    def __init__(self):
        super().__init__("MINIM")
    
    def choose_action(self, engine, state, player, dice1, dice2):
        helper = AgentHelper(engine, state, player, dice1, dice2)
        
        if helper.legal(dice1) and helper.legal(dice2):
            return Action.CHOOSE_DIE_1 if dice1 < dice2 else Action.CHOOSE_DIE_2
        elif helper.legal(dice1):
            return Action.CHOOSE_DIE_1
        elif helper.legal(dice2):
            return Action.CHOOSE_DIE_2
        else:
            return Action.SKIP


class ExactorAgent(BaseAgent):
    """Endgame precision - prioritize exact win, otherwise MAXIM."""
    
    def __init__(self):
        super().__init__("EXACTOR")
    
    def choose_action(self, engine, state, player, dice1, dice2):
        helper = AgentHelper(engine, state, player, dice1, dice2)
        
        # Check for exact win
        if helper.legal(dice1) and helper.landing(dice1) == 100:
            return Action.CHOOSE_DIE_1
        if helper.legal(dice2) and helper.landing(dice2) == 100:
            return Action.CHOOSE_DIE_2
        
        # Fall back to MAXIM
        return MaximAgent().choose_action(engine, state, player, dice1, dice2)


class SnakeAvoiderAgent(BaseAgent):
    """Avoid demotion - penalizes snake heads."""
    
    def __init__(self):
        super().__init__("SNAKE_AVOIDER")
    
    def choose_action(self, engine, state, player, dice1, dice2):
        helper = AgentHelper(engine, state, player, dice1, dice2)
        
        safe_moves = []
        for die_val, action in [(dice1, Action.CHOOSE_DIE_1), (dice2, Action.CHOOSE_DIE_2)]:
            if helper.legal(die_val) and not helper.is_snake(die_val):
                safe_moves.append((die_val, action))
        
        if safe_moves:
            # Return largest safe move
            return max(safe_moves, key=lambda x: x[0])[1]
        
        # No safe moves, choose smaller die
        if helper.legal(dice1) and helper.legal(dice2):
            return Action.CHOOSE_DIE_1 if dice1 < dice2 else Action.CHOOSE_DIE_2
        elif helper.legal(dice1):
            return Action.CHOOSE_DIE_1
        elif helper.legal(dice2):
            return Action.CHOOSE_DIE_2
        
        return Action.SKIP


class ScorpionAvoiderAgent(BaseAgent):
    """Avoid tempo loss - minimizes stun."""
    
    def __init__(self):
        super().__init__("SCORPION_AVOIDER")
    
    def choose_action(self, engine, state, player, dice1, dice2):
        helper = AgentHelper(engine, state, player, dice1, dice2)
        
        safe_moves = []
        for die_val, action in [(dice1, Action.CHOOSE_DIE_1), (dice2, Action.CHOOSE_DIE_2)]:
            if helper.legal(die_val) and not helper.is_scorpion(die_val):
                safe_moves.append((die_val, action))
        
        if safe_moves:
            # Return largest safe move
            return max(safe_moves, key=lambda x: x[0])[1]
        
        # No safe moves, choose smaller die
        if helper.legal(dice1) and helper.legal(dice2):
            return Action.CHOOSE_DIE_1 if dice1 < dice2 else Action.CHOOSE_DIE_2
        elif helper.legal(dice1):
            return Action.CHOOSE_DIE_1
        elif helper.legal(dice2):
            return Action.CHOOSE_DIE_2
        
        return Action.SKIP


class SafePreferrerAgent(BaseAgent):
    """Anchor on safe zones, otherwise avoid snakes."""
    
    def __init__(self):
        super().__init__("SAFE_PREFERRER")
    
    def choose_action(self, engine, state, player, dice1, dice2):
        helper = AgentHelper(engine, state, player, dice1, dice2)
        
        # Check for safe zone moves
        for die_val, action in [(dice1, Action.CHOOSE_DIE_1), (dice2, Action.CHOOSE_DIE_2)]:
            if helper.legal(die_val) and helper.is_safe(die_val):
                return action
        
        # Fall back to snake avoider
        return SnakeAvoiderAgent().choose_action(engine, state, player, dice1, dice2)


class HunterAgent(BaseAgent):
    """Aggressive capture - always prioritizes capture."""
    
    def __init__(self):
        super().__init__("HUNTER")
    
    def choose_action(self, engine, state, player, dice1, dice2):
        helper = AgentHelper(engine, state, player, dice1, dice2)
        
        # Check for capture moves
        for die_val, action in [(dice1, Action.CHOOSE_DIE_1), (dice2, Action.CHOOSE_DIE_2)]:
            if helper.legal(die_val) and helper.captures(die_val):
                return action
        
        # Fall back to MAXIM
        return MaximAgent().choose_action(engine, state, player, dice1, dice2)


class SafeHunterAgent(BaseAgent):
    """Smart capture - avoids useless captures near safe zones."""
    
    def __init__(self):
        super().__init__("SAFE_HUNTER")
    
    def choose_action(self, engine, state, player, dice1, dice2):
        helper = AgentHelper(engine, state, player, dice1, dice2)
        
        opponent_pos = state.get_player_position(player.opponent())
        prev_safe = engine.board.get_previous_safe_zone(opponent_pos)
        
        # Check for good capture moves (opponent not near safe zone)
        for die_val, action in [(dice1, Action.CHOOSE_DIE_1), (dice2, Action.CHOOSE_DIE_2)]:
            if helper.legal(die_val) and helper.captures(die_val):
                # Check if opponent is far from safe zone
                if opponent_pos - prev_safe > 5:  # More than 5 positions away
                    return action
        
        # Fall back to snake avoider
        return SnakeAvoiderAgent().choose_action(engine, state, player, dice1, dice2)


class AntiCaptureAgent(BaseAgent):
    """Avoid exposure - one-step opponent modeling."""
    
    def __init__(self):
        super().__init__("ANTI_CAPTURE")
    
    def choose_action(self, engine, state, player, dice1, dice2):
        helper = AgentHelper(engine, state, player, dice1, dice2)
        
        safe_moves = []
        for die_val, action in [(dice1, Action.CHOOSE_DIE_1), (dice2, Action.CHOOSE_DIE_2)]:
            if helper.legal(die_val) and not helper.opponent_can_capture(helper.final_pos(die_val)):
                safe_moves.append((die_val, action))
        
        if safe_moves:
            # Return largest safe move
            return max(safe_moves, key=lambda x: x[0])[1]
        
        # No safe moves, choose smaller die
        if helper.legal(dice1) and helper.legal(dice2):
            return Action.CHOOSE_DIE_1 if dice1 < dice2 else Action.CHOOSE_DIE_2
        elif helper.legal(dice1):
            return Action.CHOOSE_DIE_1
        elif helper.legal(dice2):
            return Action.CHOOSE_DIE_2
        
        return Action.SKIP


class GrapeSeekerAgent(BaseAgent):
    """Prioritize immunity - seeks grapes."""
    
    def __init__(self):
        super().__init__("GRAPE_SEEKER")
    
    def choose_action(self, engine, state, player, dice1, dice2):
        helper = AgentHelper(engine, state, player, dice1, dice2)
        
        # Check for grape moves
        for die_val, action in [(dice1, Action.CHOOSE_DIE_1), (dice2, Action.CHOOSE_DIE_2)]:
            if helper.legal(die_val) and helper.is_grape(die_val):
                return action
        
        # Fall back to snake avoider
        return SnakeAvoiderAgent().choose_action(engine, state, player, dice1, dice2)


class ImmuneAggressorAgent(BaseAgent):
    """Use immunity window - risk-on when immune."""
    
    def __init__(self):
        super().__init__("IMMUNE_AGGRESSOR")
    
    def choose_action(self, engine, state, player, dice1, dice2):
        immunity = state.get_player_immunity(player)
        
        if immunity > 0:
            # Risk-on: use MAXIM
            return MaximAgent().choose_action(engine, state, player, dice1, dice2)
        else:
            # Risk-off: use snake avoider
            return SnakeAvoiderAgent().choose_action(engine, state, player, dice1, dice2)


class StunExploiterAgent(BaseAgent):
    """Exploit tempo advantage - aggressive when opponent stunned."""
    
    def __init__(self):
        super().__init__("STUN_EXPLOITER")
    
    def choose_action(self, engine, state, player, dice1, dice2):
        opponent_stun = state.get_player_stun(player.opponent())
        
        if opponent_stun > 0:
            # Opponent frozen: be aggressive
            return MaximAgent().choose_action(engine, state, player, dice1, dice2)
        else:
            # Normal play: avoid scorpions
            return ScorpionAvoiderAgent().choose_action(engine, state, player, dice1, dice2)


class BalancedEvalAgent(BaseAgent):
    """Weighted evaluation function - generalist."""
    
    def __init__(self):
        super().__init__("BALANCED_EVAL")
    
    def choose_action(self, engine, state, player, dice1, dice2):
        helper = AgentHelper(engine, state, player, dice1, dice2)
        
        best_score = float('-inf')
        best_action = Action.SKIP
        
        for die_val, action in [(dice1, Action.CHOOSE_DIE_1), (dice2, Action.CHOOSE_DIE_2)]:
            if helper.legal(die_val):
                score = (
                    1.0 * helper.progress(die_val) +
                    2.0 * helper.ladder_gain(die_val) -
                    2.5 * helper.snake_loss(die_val) -
                    1.5 * helper.scorpion_penalty(die_val) +
                    1.5 * helper.grape_bonus(die_val) +
                    2.0 * helper.capture_bonus(die_val) -
                    1.5 * helper.exposure_penalty(die_val)
                )
                
                if score > best_score:
                    best_score = score
                    best_action = action
        
        return best_action


class RiskSeekerAgent(BaseAgent):
    """Volatility maximizer - aggressive high swing."""
    
    def __init__(self):
        super().__init__("RISK_SEEKER")
    
    def choose_action(self, engine, state, player, dice1, dice2):
        helper = AgentHelper(engine, state, player, dice1, dice2)
        
        best_score = float('-inf')
        best_action = Action.SKIP
        
        for die_val, action in [(dice1, Action.CHOOSE_DIE_1), (dice2, Action.CHOOSE_DIE_2)]:
            if helper.legal(die_val):
                score = (
                    1.2 * helper.progress(die_val) +
                    3.0 * helper.ladder_gain(die_val) -
                    1.0 * helper.snake_loss(die_val) -
                    0.5 * helper.scorpion_penalty(die_val) +
                    0.5 * helper.grape_bonus(die_val) +
                    3.0 * helper.capture_bonus(die_val) -
                    0.5 * helper.exposure_penalty(die_val)
                )
                
                if score > best_score:
                    best_score = score
                    best_action = action
        
        return best_action


class RiskAverseAgent(BaseAgent):
    """Minimize punishment - defensive planner."""
    
    def __init__(self):
        super().__init__("RISK_AVERSE")
    
    def choose_action(self, engine, state, player, dice1, dice2):
        helper = AgentHelper(engine, state, player, dice1, dice2)
        
        best_score = float('-inf')
        best_action = Action.SKIP
        
        for die_val, action in [(dice1, Action.CHOOSE_DIE_1), (dice2, Action.CHOOSE_DIE_2)]:
            if helper.legal(die_val):
                score = (
                    0.8 * helper.progress(die_val) +
                    1.5 * helper.ladder_gain(die_val) -
                    3.5 * helper.snake_loss(die_val) -
                    2.5 * helper.scorpion_penalty(die_val) +
                    2.0 * helper.grape_bonus(die_val) +
                    1.0 * helper.capture_bonus(die_val) -
                    2.5 * helper.exposure_penalty(die_val)
                )
                
                if score > best_score:
                    best_score = score
                    best_action = action
        
        return best_action

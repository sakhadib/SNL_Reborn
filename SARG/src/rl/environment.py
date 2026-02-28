"""
SARG Gymnasium Environment
Wraps the SARG game engine as a Gym environment for RL training.
"""

import numpy as np
import gymnasium as gym
from gymnasium import spaces
from typing import Tuple, Dict, Optional, Any
import random

from src.engine import GameEngine, GameState, Player
from src.agents import AGENT_REGISTRY, BaseAgent


class SARGEnv(gym.Env):
    """
    SARG Gym Environment for RL training.
    
    Observation Space: Box(6,) - [self_pos, self_stun, self_immune, opp_pos, opp_stun, opp_immune]
    Action Space: Discrete(3) - [use_dice_1, use_dice_2, skip]
    """
    
    metadata = {"render_modes": []}
    
    def __init__(
        self,
        opponent: Optional[BaseAgent] = None,
        opponent_id: Optional[str] = None,
        config: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize SARG environment.
        
        Args:
            opponent: Opponent agent instance (if None, uses random agent)
            opponent_id: Opponent agent ID from registry (alternative to opponent)
            config: Environment configuration
        """
        super().__init__()
        
        # Configuration
        self.config = config or {}
        self.win_base_reward = self.config.get("win_base_reward", 100.0)
        self.loss_base_reward = self.config.get("loss_base_reward", -100.0)
        self.margin_alpha = self.config.get("margin_alpha", 0.75)
        self.step_penalty = self.config.get("step_penalty", 0.1)
        
        # Game engine
        self.engine = GameEngine()
        
        # Opponent setup
        if opponent is not None:
            self.opponent = opponent
        elif opponent_id is not None:
            if opponent_id == "random":
                self.opponent = None  # Random opponent handled separately
            else:
                self.opponent = AGENT_REGISTRY[opponent_id]()
        else:
            self.opponent = None  # Random opponent by default
        
        # RL player assignment (randomly assigned each episode)
        self.rl_player = Player.A
        
        # Observation space: [self_pos, self_stun, self_immune, opp_pos, opp_stun, opp_immune]
        self.observation_space = spaces.Box(
            low=0.0,
            high=1.0,
            shape=(6,),
            dtype=np.float32
        )
        
        # Action space: [use_dice_1, use_dice_2, skip]
        self.action_space = spaces.Discrete(3)
        
        # Episode state
        self.state: Optional[GameState] = None
        self.dice1: int = 0
        self.dice2: int = 0
        self.episode_reward: float = 0.0
        self.episode_length: int = 0
        
    def reset(
        self,
        seed: Optional[int] = None,
        options: Optional[Dict[str, Any]] = None
    ) -> Tuple[np.ndarray, Dict[str, Any]]:
        """
        Reset environment for new episode.
        
        Args:
            seed: Random seed
            options: Additional options (can include 'rl_player' to force player assignment)
            
        Returns:
            observation: Initial observation
            info: Additional info
        """
        super().reset(seed=seed)
        
        if seed is not None:
            random.seed(seed)
            np.random.seed(seed)
        
        # Randomly assign RL player (or use provided option)
        if options and 'rl_player' in options:
            self.rl_player = options['rl_player']
        else:
            self.rl_player = random.choice([Player.A, Player.B])
        
        # Initialize game state
        self.state = GameState.initial_state(self.engine.board)
        self.episode_reward = 0.0
        self.episode_length = 0
        
        # If opponent goes first, play their move(s) until RL agent's turn
        while self.state.current_player != self.rl_player and not self.state.is_terminal():
            self._play_opponent_move()
        
        # Roll dice for RL agent
        self.dice1, self.dice2 = self._roll_dice()
        
        observation = self._get_observation()
        info = self._get_info()
        
        return observation, info
    
    def step(self, action: int) -> Tuple[np.ndarray, float, bool, bool, Dict[str, Any]]:
        """
        Execute one step in the environment.
        
        Args:
            action: Action to take (0=dice1, 1=dice2, 2=skip)
            
        Returns:
            observation: Next observation
            reward: Step reward
            terminated: Whether episode ended
            truncated: Whether episode was truncated (always False)
            info: Additional info
        """
        assert self.state is not None, "Must call reset() before step()"
        assert self.state.current_player == self.rl_player, "Not RL agent's turn"
        
        # Map action to engine action
        if action == 0:
            engine_action = 0  # Use dice 1
        elif action == 1:
            engine_action = 1  # Use dice 2
        else:
            engine_action = 2  # Skip
        
        # Execute RL agent's move
        self.state, move_info = self.engine.execute_move(
            self.state, self.dice1, self.dice2, engine_action
        )
        
        # Step penalty
        step_reward = -self.step_penalty
        self.episode_length += 1
        
        # Check if game ended
        if self.state.is_terminal():
            terminal_reward = self._calculate_terminal_reward()
            total_reward = step_reward + terminal_reward
            self.episode_reward += total_reward
            
            observation = self._get_observation()
            info = self._get_info()
            info['episode_reward'] = self.episode_reward
            info['episode_length'] = self.episode_length
            
            return observation, total_reward, True, False, info
        
        # Opponent's turn(s) until RL agent's turn or game ends
        while self.state.current_player != self.rl_player and not self.state.is_terminal():
            self._play_opponent_move()
        
        # Check again if game ended after opponent's move(s)
        if self.state.is_terminal():
            terminal_reward = self._calculate_terminal_reward()
            total_reward = step_reward + terminal_reward
            self.episode_reward += total_reward
            
            observation = self._get_observation()
            info = self._get_info()
            info['episode_reward'] = self.episode_reward
            info['episode_length'] = self.episode_length
            
            return observation, total_reward, True, False, info
        
        # Roll new dice for RL agent
        self.dice1, self.dice2 = self._roll_dice()
        
        # Only step penalty for non-terminal steps
        self.episode_reward += step_reward
        
        observation = self._get_observation()
        info = self._get_info()
        
        return observation, step_reward, False, False, info
    
    def _play_opponent_move(self):
        """Play one opponent move."""
        # Roll dice for opponent
        dice1, dice2 = self._roll_dice()
        
        # Get opponent action
        if self.opponent is None:
            # Random opponent: choose random valid action
            valid_actions = self.engine.get_legal_actions(self.state, dice1, dice2)
            action = random.choice(valid_actions)
        else:
            # Use opponent agent
            action = self.opponent.choose_action(
                self.engine,
                self.state,
                self.state.current_player,
                dice1,
                dice2
            )
        
        # Execute opponent move
        self.state, move_info = self.engine.execute_move(self.state, dice1, dice2, action)
        self.episode_length += 1
    
    def _roll_dice(self) -> Tuple[int, int]:
        """Roll two dice."""
        return random.randint(1, 6), random.randint(1, 6)
    
    def _get_observation(self) -> np.ndarray:
        """
        Get current observation.
        
        Returns:
            Observation vector [self_pos, self_stun, self_immune, opp_pos, opp_stun, opp_immune]
        """
        if self.rl_player == Player.A:
            observation = np.array([
                self.state.a_position / 100.0,
                self.state.a_stun / 3.0,
                self.state.a_immunity / 3.0,
                self.state.b_position / 100.0,
                self.state.b_stun / 3.0,
                self.state.b_immunity / 3.0,
            ], dtype=np.float32)
        else:
            observation = np.array([
                self.state.b_position / 100.0,
                self.state.b_stun / 3.0,
                self.state.b_immunity / 3.0,
                self.state.a_position / 100.0,
                self.state.a_stun / 3.0,
                self.state.a_immunity / 3.0,
            ], dtype=np.float32)
        
        return observation
    
    def _get_info(self) -> Dict[str, Any]:
        """Get additional info dictionary."""
        return {
            'rl_player': self.rl_player,
            'dice1': self.dice1,
            'dice2': self.dice2,
            'episode_length': self.episode_length,
        }
    
    def _calculate_terminal_reward(self) -> float:
        """
        Calculate terminal reward based on game outcome.
        
        Returns:
            Terminal reward (win/loss with margin scaling)
        """
        winner = self.state.get_winner()
        loser_pos = self.state.get_loser_final_position()
        
        # Calculate margin multiplier (same as Elo system)
        margin = 100 - loser_pos
        margin_multiplier = 1 + self.margin_alpha * (margin / 100.0)
        
        # RL agent won
        if winner == self.rl_player:
            reward = self.win_base_reward * margin_multiplier
        else:
            reward = self.loss_base_reward * margin_multiplier
        
        return reward
    
    def action_masks(self) -> np.ndarray:
        """
        Get action mask for current state.
        
        Returns:
            Binary mask [1, 1, 1] where 1=valid, 0=invalid
        """
        if self.state is None:
            return np.ones(3, dtype=np.int8)
        
        mask = np.ones(3, dtype=np.int8)
        
        # Get RL player's position and stun status
        if self.rl_player == Player.A:
            current_pos = self.state.a_position
            stun = self.state.a_stun
        else:
            current_pos = self.state.b_position
            stun = self.state.b_stun
        
        # If stunned, can only skip
        if stun > 0:
            mask[0] = 0  # Cannot use dice 1
            mask[1] = 0  # Cannot use dice 2
            return mask
        
        # Check if dice moves are legal
        if current_pos + self.dice1 > 100:
            mask[0] = 0  # Dice 1 illegal
        
        if current_pos + self.dice2 > 100:
            mask[1] = 0  # Dice 2 illegal
        
        return mask
    
    def set_opponent(self, opponent: BaseAgent = None, opponent_id: str = None):
        """
        Change opponent during training.
        
        Args:
            opponent: New opponent agent instance
            opponent_id: New opponent agent ID from registry
        """
        if opponent is not None:
            self.opponent = opponent
        elif opponent_id is not None:
            if opponent_id == "random":
                self.opponent = None
            else:
                self.opponent = AGENT_REGISTRY[opponent_id]()
        else:
            self.opponent = None


class RandomOpponent:
    """Dummy class for random opponent (for compatibility)."""
    pass

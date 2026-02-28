"""
RL Agent Wrapper
Wraps MaskablePPO from sb3-contrib with save/load and prediction interface.
"""

import numpy as np
from pathlib import Path
from typing import Optional, Dict, Any, Tuple
from sb3_contrib import MaskablePPO
from sb3_contrib.common.maskable.policies import MaskableActorCriticPolicy
from sb3_contrib.common.wrappers import ActionMasker
import torch

from src.rl.environment import SARGEnv
from src.engine import Player


class RLAgent:
    """
    RL Agent wrapper for SARG using MaskablePPO.
    """
    
    def __init__(
        self,
        env: Optional[SARGEnv] = None,
        config: Optional[Dict[str, Any]] = None,
        model_path: Optional[Path] = None
    ):
        """
        Initialize RL agent.
        
        Args:
            env: SARG environment (if None, must load from model_path)
            config: Training configuration
            model_path: Path to load existing model
        """
        self.config = config or {}
        self.env = env
        self.model = None
        
        if model_path is not None and Path(model_path).exists():
            self.load(model_path)
        elif env is not None:
            self._create_model()
        else:
            raise ValueError("Must provide either env or model_path")
    
    def _create_model(self):
        """Create new MaskablePPO model."""
        # Wrap environment with action masker
        def mask_fn(env: SARGEnv) -> np.ndarray:
            return env.action_masks()
        
        masked_env = ActionMasker(self.env, mask_fn)
        
        # Extract hyperparameters from config
        policy_kwargs = {
            "net_arch": [
                self.config.get("hidden_size", 256)
            ] * self.config.get("n_layers", 2)
        }
        
        self.model = MaskablePPO(
            policy=MaskableActorCriticPolicy,
            env=masked_env,
            learning_rate=self.config.get("learning_rate", 3e-4),
            n_steps=self.config.get("n_steps", 2048),
            batch_size=self.config.get("batch_size", 2048),
            n_epochs=self.config.get("n_epochs", 10),
            gamma=self.config.get("gamma", 0.99),
            gae_lambda=self.config.get("gae_lambda", 0.95),
            clip_range=self.config.get("clip_range", 0.2),
            ent_coef=self.config.get("ent_coef", 0.01),
            vf_coef=self.config.get("vf_coef", 0.5),
            max_grad_norm=self.config.get("max_grad_norm", 0.5),
            target_kl=self.config.get("target_kl", None),
            policy_kwargs=policy_kwargs,
            verbose=0,  # Disable SB3 verbose output (we use custom console callback)
            tensorboard_log=None,  # Disable tensorboard for now
            seed=self.config.get("seed", None)
        )
    
    def train(self, total_timesteps: int, **kwargs):
        """
        Train the model.
        
        Args:
            total_timesteps: Number of timesteps to train
            **kwargs: Additional arguments for model.learn()
        """
        self.model.learn(total_timesteps=total_timesteps, **kwargs)
    
    def predict(
        self,
        observation: np.ndarray,
        action_mask: Optional[np.ndarray] = None,
        deterministic: bool = False
    ) -> Tuple[int, Optional[np.ndarray]]:
        """
        Predict action from observation.
        
        Args:
            observation: Current observation
            action_mask: Action mask (if None, uses all actions)
            deterministic: Whether to use deterministic policy
            
        Returns:
            action: Selected action
            state: Internal state (None for feedforward policies)
        """
        if action_mask is None:
            action_mask = np.ones(3, dtype=np.int8)
        
        action, state = self.model.predict(
            observation,
            action_masks=action_mask,
            deterministic=deterministic
        )
        
        return int(action), state
    
    def choose_action(
        self,
        engine,
        state,
        player: Player,
        dice1: int,
        dice2: int,
        deterministic: bool = False
    ) -> int:
        """
        Choose action using RL policy (compatible with BaseAgent interface).
        
        Args:
            engine: Game engine
            state: Current game state
            player: Current player
            dice1: First dice value
            dice2: Second dice value
            deterministic: Whether to use deterministic policy
            
        Returns:
            action: Selected action (0=dice1, 1=dice2, 2=skip)
        """
        # Build observation
        if player == Player.A:
            observation = np.array([
                state.a_position / 100.0,
                state.a_stun / 3.0,
                state.a_immunity / 3.0,
                state.b_position / 100.0,
                state.b_stun / 3.0,
                state.b_immunity / 3.0,
            ], dtype=np.float32)
        else:
            observation = np.array([
                state.b_position / 100.0,
                state.b_stun / 3.0,
                state.b_immunity / 3.0,
                state.a_position / 100.0,
                state.a_stun / 3.0,
                state.a_immunity / 3.0,
            ], dtype=np.float32)
        
        # Build action mask
        action_mask = np.ones(3, dtype=np.int8)
        
        if player == Player.A:
            current_pos = state.a_position
            stun = state.a_stun
        else:
            current_pos = state.b_position
            stun = state.b_stun
        
        if stun > 0:
            action_mask[0] = 0
            action_mask[1] = 0
        else:
            if current_pos + dice1 > 100:
                action_mask[0] = 0
            if current_pos + dice2 > 100:
                action_mask[1] = 0
        
        # Predict action
        action, _ = self.predict(observation, action_mask, deterministic)
        
        return action
    
    def save(self, path: Path):
        """
        Save model to disk.
        
        Args:
            path: Path to save model (will create parent directories)
        """
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        self.model.save(str(path))
    
    def load(self, path: Path):
        """
        Load model from disk.
        
        Args:
            path: Path to load model from
        """
        path = Path(path)
        if not path.exists():
            raise FileNotFoundError(f"Model not found: {path}")
        
        self.model = MaskablePPO.load(str(path))
        
        # Extract environment from model
        if hasattr(self.model, 'env') and self.model.env is not None:
            # Unwrap ActionMasker to get SARGEnv
            env = self.model.env
            if hasattr(env, 'env'):
                self.env = env.env
            else:
                self.env = env
    
    def get_model(self) -> MaskablePPO:
        """Get underlying MaskablePPO model."""
        return self.model
    
    def set_env(self, env: SARGEnv):
        """
        Set new environment for the model.
        
        Args:
            env: New SARG environment
        """
        self.env = env
        
        # Wrap with action masker
        def mask_fn(e: SARGEnv) -> np.ndarray:
            return e.action_masks()
        
        masked_env = ActionMasker(env, mask_fn)
        self.model.set_env(masked_env)


def create_rl_agent(config: Dict[str, Any], opponent_id: str = "random") -> RLAgent:
    """
    Factory function to create RL agent with environment.
    
    Args:
        config: Training configuration
        opponent_id: Initial opponent ID
        
    Returns:
        Initialized RL agent
    """
    env = SARGEnv(opponent_id=opponent_id, config=config)
    agent = RLAgent(env=env, config=config)
    return agent

"""
RL Training Configuration
Contains all hyperparameters and training settings for SARG RL-V1 agent.
"""

from pathlib import Path
from typing import Dict, Any


# Default hyperparameters for PPO training
DEFAULT_CONFIG: Dict[str, Any] = {
    # ==================== Network Architecture ====================
    "policy_type": "MlpPolicy",
    "hidden_size": 256,
    "n_layers": 2,
    "activation": "tanh",
    
    # ==================== PPO Hyperparameters ====================
    "learning_rate": 3e-4,
    "n_steps": 2048,           # Rollout buffer size
    "batch_size": 2048,        # Minibatch size for optimization
    "n_epochs": 10,            # Optimization epochs per rollout
    "gamma": 0.99,             # Discount factor
    "gae_lambda": 0.95,        # GAE smoothing parameter
    "clip_range": 0.2,         # PPO clipping parameter
    "ent_coef": 0.01,          # Entropy coefficient (exploration)
    "vf_coef": 0.5,            # Value function loss coefficient
    "max_grad_norm": 0.5,      # Gradient clipping
    "target_kl": None,         # No early stopping
    
    # ==================== Reward Structure ====================
    "win_base_reward": 10.0,      # Reduced from 100 to 10 for stable learning
    "loss_base_reward": -10.0,    # Reduced from -100 to -10
    "margin_alpha": 0.75,         # Margin sensitivity (same as Elo)
    "step_penalty": 0.01,         # Reduced from 0.1 to 0.01
    
    # ==================== Curriculum Training ====================
    # Phase 1: Random Opponent
    "phase_1_min_episodes": 150000,  # Lower threshold to avoid saturation
    "phase_1_max_episodes": 200000,
    "phase_1_target_wr": 0.88,  # Realistic stable threshold (currently achieving this)
    
    # Phase 2: Weak Heuristics (MAXIM, MINIM, EXACTOR)
    "phase_2_min_episodes": 200000,
    "phase_2_max_episodes": 500000,
    "phase_2_target_wr": 0.60,
    "phase_2_opponents": ["maxim", "minim", "exactor"],
    
    # Phase 3: All Heuristics
    "phase_3_min_episodes": 500000,
    "phase_3_max_episodes": 1000000,
    "phase_3_target_wr": 0.55,
    "phase_3_opponents": "all",  # All 15 heuristic agents
    
    # Phase 4: Self-Play
    "phase_4_min_episodes": 1500000,
    "phase_4_max_episodes": 2000000,
    "phase_4_snapshot_freq": 100000,    # Save snapshot every N episodes
    "phase_4_snapshot_pool_size": 5,     # Keep last N snapshots
    "phase_4_self_play_ratio": 0.7,     # 70% vs snapshots, 30% vs top heuristics
    "phase_4_top_heuristics": ["risk_seeker", "risk_averse", "balanced_eval", 
                                "snake_avoider", "stun_exploiter"],
    
    # ==================== Checkpointing ====================
    "checkpoint_freq": 10000,           # Save checkpoint every N episodes
    "save_best": True,                  # Save best model separately
    "checkpoint_dir": "data/rl_checkpoints",
    "snapshot_dir": "data/rl_checkpoints/snapshots",
    
    # ==================== Evaluation ====================
    "eval_freq": 50000,                 # Evaluate every N episodes
    "eval_games_per_opponent": 100,     # Games per opponent during eval
    "eval_alternating_start": True,     # Alternate starting player
    "eval_dir": "data/rl_evaluation",
    
    # ==================== Logging ====================
    "log_dir": "data/rl_logs",
    "tensorboard_log": False,  # Disabled until tensorboard installed
    "console_log_freq": 100,            # Print to console every N episodes
    "win_rate_window": 5000,            # Rolling window for win rate calculation
    
    # ==================== Reproducibility ====================
    "seed": 42,
    "deterministic_eval": True,         # Use deterministic policy during eval
    
    # ==================== Performance ====================
    "device": "auto",                 # auto, cpu, or cuda
    "n_envs": 1,                        # Number of parallel environments (1 for simplicity)
    "verbose": 1,                       # SB3 verbosity level
}


def get_config(overrides: Dict[str, Any] = None) -> Dict[str, Any]:
    """
    Get configuration with optional overrides.
    
    Args:
        overrides: Dictionary of config keys to override
        
    Returns:
        Complete configuration dictionary
    """
    config = DEFAULT_CONFIG.copy()
    if overrides:
        config.update(overrides)
    return config


def get_phase_config(phase: int, config: Dict[str, Any] = None) -> Dict[str, Any]:
    """
    Get phase-specific configuration.
    
    Args:
        phase: Training phase (1-4)
        config: Base configuration (uses DEFAULT_CONFIG if None)
        
    Returns:
        Phase-specific settings
    """
    if config is None:
        config = DEFAULT_CONFIG
    
    phase_config = {
        "phase": phase,
        "min_episodes": config[f"phase_{phase}_min_episodes"],
        "max_episodes": config[f"phase_{phase}_max_episodes"],
    }
    
    if phase == 1:
        phase_config["target_wr"] = config["phase_1_target_wr"]
        phase_config["opponents"] = ["random"]
        
    elif phase == 2:
        phase_config["target_wr"] = config["phase_2_target_wr"]
        phase_config["opponents"] = config["phase_2_opponents"]
        
    elif phase == 3:
        phase_config["target_wr"] = config["phase_3_target_wr"]
        phase_config["opponents"] = config["phase_3_opponents"]
        
    elif phase == 4:
        # Phase 4 has no target win rate (trains until max episodes)
        phase_config["snapshot_freq"] = config["phase_4_snapshot_freq"]
        phase_config["snapshot_pool_size"] = config["phase_4_snapshot_pool_size"]
        phase_config["self_play_ratio"] = config["phase_4_self_play_ratio"]
        phase_config["top_heuristics"] = config["phase_4_top_heuristics"]
    
    return phase_config


def create_directories(config: Dict[str, Any]):
    """Create all necessary directories for training."""
    Path(config["checkpoint_dir"]).mkdir(parents=True, exist_ok=True)
    Path(config["snapshot_dir"]).mkdir(parents=True, exist_ok=True)
    Path(config["eval_dir"]).mkdir(parents=True, exist_ok=True)
    Path(config["log_dir"]).mkdir(parents=True, exist_ok=True)

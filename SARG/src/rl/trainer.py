"""
Curriculum Trainer
4-phase training pipeline with automatic progression.
"""

import json
import random
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime

from src.rl.environment import SARGEnv
from src.rl.rl_agent import RLAgent
from src.rl.config import get_phase_config
from src.agents import AGENT_REGISTRY


class CurriculumTrainer:
    """
    Manages 4-phase curriculum training with automatic progression.
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize curriculum trainer.
        
        Args:
            config: Training configuration
        """
        self.config = config
        self.current_phase = 1
        self.total_episodes = 0
        self.phase_episodes = 0
        
        # Training state tracking
        self.best_win_rate = 0.0
        self.recent_win_rate = 0.0
        self.phase_win_rates = {}
        
        # Episode history (for win rate calculation)
        self.recent_results = []  # List of (opponent_id, won) tuples
        self.win_rate_window = config.get("win_rate_window", 5000)
        
        # Snapshots for Phase 4
        self.snapshots = []  # List of (episode_num, model_path) tuples
        
        # Create agent and environment
        self.agent = None
        self.env = None
        
        # Load existing training state if resuming
        self.training_state_path = Path(config["checkpoint_dir"]) / "training_state.json"
        if self.training_state_path.exists():
            self._load_training_state()
    
    def initialize_training(self, resume: bool = False):
        """
        Initialize or resume training.
        
        Args:
            resume: Whether to resume from checkpoint
        """
        if resume and (Path(self.config["checkpoint_dir"]) / "rl_v1_latest.zip").exists():
            print("Resuming training from checkpoint...")
            self._resume_from_checkpoint()
        else:
            print("Starting new training...")
            self._start_new_training()
    
    def _start_new_training(self):
        """Start new training from scratch."""
        self.current_phase = 1
        self.total_episodes = 0
        self.phase_episodes = 0
        
        # Create environment with random opponent (Phase 1)
        self.env = SARGEnv(opponent_id="random", config=self.config)
        
        # Create RL agent
        self.agent = RLAgent(env=self.env, config=self.config)
        
        # Save initial state
        self._save_training_state()
    
    def _resume_from_checkpoint(self):
        """Resume training from checkpoint."""
        # Load training state
        self._load_training_state()
        
        # Create environment with appropriate opponent for current phase
        phase_config = get_phase_config(self.current_phase, self.config)
        opponent_id = self._get_current_opponent(phase_config)
        self.env = SARGEnv(opponent_id=opponent_id, config=self.config)
        
        # Load model
        checkpoint_path = Path(self.config["checkpoint_dir"]) / "rl_v1_latest.zip"
        self.agent = RLAgent(model_path=checkpoint_path, config=self.config)
        self.agent.set_env(self.env)
        
        print(f"Resumed from episode {self.total_episodes}, phase {self.current_phase}")
    
    def train_phase(self, phase: int, max_episodes: Optional[int] = None):
        """
        Train a specific phase.
        
        Args:
            phase: Phase number (1-4)
            max_episodes: Maximum episodes for this phase (overrides config)
        """
        phase_config = get_phase_config(phase, self.config)
        
        if max_episodes is None:
            max_episodes = phase_config["max_episodes"]
        
        min_episodes = phase_config["min_episodes"]
        target_wr = phase_config.get("target_wr", None)
        
        print(f"\n{'='*70}")
        print(f"Phase {phase}: {self._get_phase_name(phase)}")
        print(f"{'='*70}")
        print(f"Min episodes: {min_episodes:,}")
        print(f"Max episodes: {max_episodes:,}")
        if target_wr:
            print(f"Target win rate: {target_wr:.1%}")
        print()
        
        phase_start_episodes = self.total_episodes
        
        # Train until phase completion criteria met
        while self.phase_episodes < max_episodes:
            # Check if minimum episodes met and target win rate achieved
            if target_wr and self.phase_episodes >= min_episodes:
                if self.recent_win_rate >= target_wr:
                    print(f"\n✓ Phase {phase} completed!")
                    print(f"  Episodes: {self.phase_episodes:,}")
                    print(f"  Final win rate: {self.recent_win_rate:.1%}")
                    break
            
            # Play one episode
            self._play_episode(phase_config)
            
            # Update counters
            self.total_episodes += 1
            self.phase_episodes += 1
            
            # Periodic logging, checkpointing, evaluation handled by callbacks
        
        # Save final phase stats
        self.phase_win_rates[phase] = self.recent_win_rate
        self._save_training_state()
    
    def train_curriculum(self, start_phase: int = 1):
        """
        Train full curriculum from start_phase to Phase 4.
        
        Args:
            start_phase: Phase to start from (1-4)
        """
        for phase in range(start_phase, 5):
            self.current_phase = phase
            self.phase_episodes = 0
            self.recent_results = []
            
            # Update opponent for new phase
            self._update_opponent_for_phase(phase)
            
            # Train phase
            self.train_phase(phase)
            
            # Check if should continue to next phase
            if phase < 4:
                phase_config = get_phase_config(phase, self.config)
                if "target_wr" in phase_config:
                    if self.recent_win_rate < phase_config["target_wr"]:
                        print(f"\nWarning: Phase {phase} target not met, but continuing...")
    
    def _play_episode(self, phase_config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Play one training episode.
        
        Args:
            phase_config: Configuration for current phase
            
        Returns:
            Episode info dict
        """
        # Select opponent (important for Phases 2-4)
        opponent_id = self._get_current_opponent(phase_config)
        
        # Update environment opponent if changed
        if hasattr(self.env, 'opponent'):
            current_opponent_id = self._get_opponent_id(self.env.opponent)
            if current_opponent_id != opponent_id:
                self.env.set_opponent(opponent_id=opponent_id)
        
        # Reset environment
        obs, info = self.env.reset()
        done = False
        episode_reward = 0
        episode_length = 0
        
        # Play episode
        while not done:
            # Get action from policy
            action_mask = self.env.action_masks()
            action, _ = self.agent.predict(obs, action_mask, deterministic=False)
            
            # Step environment
            obs, reward, terminated, truncated, info = self.env.step(action)
            done = terminated or truncated
            
            episode_reward += reward
            episode_length += 1
        
        # Record result
        won = episode_reward > 0
        self.recent_results.append((opponent_id, won))
        
        # Trim window
        if len(self.recent_results) > self.win_rate_window:
            self.recent_results = self.recent_results[-self.win_rate_window:]
        
        # Update win rate
        self._update_win_rate()
        
        return {
            "opponent": opponent_id,
            "won": won,
            "reward": episode_reward,
            "length": episode_length,
        }
    
    def _update_opponent_for_phase(self, phase: int):
        """Update environment opponent for new phase."""
        phase_config = get_phase_config(phase, self.config)
        opponent_id = self._get_current_opponent(phase_config)
        self.env.set_opponent(opponent_id=opponent_id)
    
    def _get_current_opponent(self, phase_config: Dict[str, Any]) -> str:
        """
        Get current opponent ID based on phase configuration.
        
        Args:
            phase_config: Phase configuration
            
        Returns:
            Opponent ID
        """
        if self.current_phase == 1:
            return "random"
        
        elif self.current_phase == 2:
            # Randomly select from weak heuristics
            opponents = phase_config["opponents"]
            return random.choice(opponents)
        
        elif self.current_phase == 3:
            # Randomly select from all heuristics
            return random.choice(list(AGENT_REGISTRY.keys()))
        
        elif self.current_phase == 4:
            # Mix of self-play and top heuristics
            self_play_ratio = phase_config["self_play_ratio"]
            
            if random.random() < self_play_ratio and len(self.snapshots) > 0:
                # Play against snapshot
                return f"snapshot_{random.choice(self.snapshots)[0]}"
            else:
                # Play against top heuristic
                return random.choice(phase_config["top_heuristics"])
        
        return "random"
    
    def _get_opponent_id(self, opponent) -> str:
        """Get string ID of opponent agent."""
        if opponent is None:
            return "random"
        
        # Find opponent in registry
        for agent_id, agent_class in AGENT_REGISTRY.items():
            if isinstance(opponent, agent_class):
                return agent_id
        
        return "unknown"
    
    def _update_win_rate(self):
        """Update recent win rate from results window."""
        if len(self.recent_results) == 0:
            self.recent_win_rate = 0.0
            return
        
        wins = sum(1 for _, won in self.recent_results if won)
        self.recent_win_rate = wins / len(self.recent_results)
        
        # Update best win rate
        if self.recent_win_rate > self.best_win_rate:
            self.best_win_rate = self.recent_win_rate
    
    def _get_phase_name(self, phase: int) -> str:
        """Get human-readable phase name."""
        names = {
            1: "Random Opponent (Exploration)",
            2: "Weak Heuristics (Fundamentals)",
            3: "All Heuristics (Mastery)",
            4: "Self-Play (Superhuman)"
        }
        return names.get(phase, f"Unknown Phase {phase}")
    
    def save_snapshot(self):
        """Save current model as snapshot for Phase 4 self-play."""
        snapshot_dir = Path(self.config["snapshot_dir"])
        snapshot_dir.mkdir(parents=True, exist_ok=True)
        
        snapshot_path = snapshot_dir / f"snapshot_{self.total_episodes}.zip"
        self.agent.save(snapshot_path)
        
        self.snapshots.append((self.total_episodes, snapshot_path))
        
        # Keep only last N snapshots
        max_snapshots = self.config.get("phase_4_snapshot_pool_size", 5)
        if len(self.snapshots) > max_snapshots:
            # Remove oldest snapshot
            old_episode, old_path = self.snapshots.pop(0)
            if old_path.exists():
                old_path.unlink()
    
    def _save_training_state(self):
        """Save training state to JSON."""
        state = {
            "total_episodes": self.total_episodes,
            "current_phase": self.current_phase,
            "phase_episodes": self.phase_episodes,
            "best_win_rate": self.best_win_rate,
            "recent_win_rate": self.recent_win_rate,
            "phase_win_rates": self.phase_win_rates,
            "last_checkpoint": datetime.now().isoformat(),
            "snapshots": [(ep, str(path)) for ep, path in self.snapshots],
        }
        
        self.training_state_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.training_state_path, 'w') as f:
            json.dump(state, f, indent=2)
    
    def _load_training_state(self):
        """Load training state from JSON."""
        if not self.training_state_path.exists():
            return
        
        with open(self.training_state_path, 'r') as f:
            state = json.load(f)
        
        self.total_episodes = state.get("total_episodes", 0)
        self.current_phase = state.get("current_phase", 1)
        self.phase_episodes = state.get("phase_episodes", 0)
        self.best_win_rate = state.get("best_win_rate", 0.0)
        self.recent_win_rate = state.get("recent_win_rate", 0.0)
        self.phase_win_rates = state.get("phase_win_rates", {})
        self.snapshots = [(ep, Path(path)) for ep, path in state.get("snapshots", [])]
    
    def get_training_summary(self) -> Dict[str, Any]:
        """Get current training summary."""
        return {
            "total_episodes": self.total_episodes,
            "current_phase": self.current_phase,
            "phase_name": self._get_phase_name(self.current_phase),
            "phase_episodes": self.phase_episodes,
            "recent_win_rate": self.recent_win_rate,
            "best_win_rate": self.best_win_rate,
            "phase_win_rates": self.phase_win_rates,
        }

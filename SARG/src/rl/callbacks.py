"""
Training Callbacks
Handles checkpointing, evaluation, and monitoring during training.
"""

from pathlib import Path
from typing import Dict, Any
from stable_baselines3.common.callbacks import BaseCallback

from src.rl.evaluator import Evaluator


class CheckpointCallback(BaseCallback):
    """
    Callback for saving model checkpoints.
    """
    
    def __init__(
        self,
        checkpoint_freq: int,
        checkpoint_dir: str,
        save_best: bool = True,
        trainer = None,
        verbose: int = 0
    ):
        """
        Initialize checkpoint callback.
        
        Args:
            checkpoint_freq: Save checkpoint every N episodes
            checkpoint_dir: Directory to save checkpoints
            save_best: Whether to save best model separately
            trainer: CurriculumTrainer instance
            verbose: Verbosity level
        """
        super().__init__(verbose)
        self.checkpoint_freq = checkpoint_freq
        self.checkpoint_dir = Path(checkpoint_dir)
        self.save_best = save_best
        self.trainer = trainer
        self.checkpoint_dir.mkdir(parents=True, exist_ok=True)
        
        self.best_win_rate = 0.0
        self.episode_count = 0
    
    def _on_step(self) -> bool:
        """
        Called after each environment step.
        
        Returns:
            True to continue training
        """
        # Check if episode just finished
        if self.locals.get('dones', [False])[0]:
            self.episode_count += 1
            
            # Save checkpoint
            if self.episode_count % self.checkpoint_freq == 0:
                self._save_checkpoint()
                
                # Update trainer state
                if self.trainer:
                    self.trainer._save_training_state()
        
        return True
    
    def _save_checkpoint(self):
        """Save model checkpoint."""
        # Save latest
        latest_path = self.checkpoint_dir / "rl_v1_latest.zip"
        self.model.save(str(latest_path))
        
        # Save periodic snapshot
        snapshot_path = self.checkpoint_dir / f"rl_v1_episode_{self.episode_count:08d}.zip"
        self.model.save(str(snapshot_path))
        
        # Save best if win rate improved
        if self.trainer and self.save_best:
            if self.trainer.recent_win_rate > self.best_win_rate:
                self.best_win_rate = self.trainer.recent_win_rate
                best_path = self.checkpoint_dir / "rl_v1_best.zip"
                self.model.save(str(best_path))
                
                if self.verbose > 0:
                    print(f"New best model saved! Win rate: {self.best_win_rate:.1%}")


class EvaluationCallback(BaseCallback):
    """
    Callback for periodic evaluation against heuristics.
    """
    
    def __init__(
        self,
        eval_freq: int,
        evaluator: Evaluator,
        trainer = None,
        verbose: int = 0
    ):
        """
        Initialize evaluation callback.
        
        Args:
            eval_freq: Evaluate every N episodes
            evaluator: Evaluator instance
            trainer: CurriculumTrainer instance
            verbose: Verbosity level
        """
        super().__init__(verbose)
        self.eval_freq = eval_freq
        self.evaluator = evaluator
        self.trainer = trainer
        
        self.episode_count = 0
    
    def _on_step(self) -> bool:
        """
        Called after each environment step.
        
        Returns:
            True to continue training
        """
        # Check if episode just finished
        if self.locals.get('dones', [False])[0]:
            self.episode_count += 1
            
            # Run evaluation
            if self.episode_count % self.eval_freq == 0:
                self._run_evaluation()
        
        return True
    
    def _run_evaluation(self):
        """Run evaluation against all heuristics."""
        from src.rl.rl_agent import RLAgent
        
        # Wrap model in RLAgent for evaluation
        agent = RLAgent(env=None, config={})
        agent.model = self.model
        
        # Get current phase
        phase = self.trainer.current_phase if self.trainer else 1
        
        # Run evaluation
        self.evaluator.evaluate(
            agent=agent,
            opponents=None,  # All heuristics
            episode_num=self.episode_count,
            phase=phase
        )


class ConsoleCallback(BaseCallback):
    """
    Callback for console logging and progress tracking.
    """
    
    def __init__(
        self,
        log_freq: int,
        trainer = None,
        verbose: int = 1
    ):
        """
        Initialize console callback.
        
        Args:
            log_freq: Log to console every N episodes
            trainer: CurriculumTrainer instance
            verbose: Verbosity level
        """
        super().__init__(verbose)
        self.log_freq = log_freq
        self.trainer = trainer
        
        self.episode_count = 0
        self.last_episode_reward = 0
        self.last_episode_length = 0
    
    def _on_step(self) -> bool:
        """
        Called after each environment step.
        
        Returns:
            True to continue training
        """
        # Check if episode just finished
        if self.locals.get('dones', [False])[0]:
            self.episode_count += 1
            
            # Get episode info
            infos = self.locals.get('infos', [{}])
            if len(infos) > 0:
                self.last_episode_reward = infos[0].get('episode_reward', 0)
                self.last_episode_length = infos[0].get('episode_length', 0)
            
            # Log to console
            if self.episode_count % self.log_freq == 0 and self.verbose > 0:
                self._log_progress()
        
        return True
    
    def _log_progress(self):
        """Log training progress to console."""
        if self.trainer:
            summary = self.trainer.get_training_summary()
            
            print(f"Episode {summary['total_episodes']:,} | "
                  f"Phase {summary['current_phase']} | "
                  f"WR: {summary['recent_win_rate']:.1%} | "
                  f"Best: {summary['best_win_rate']:.1%} | "
                  f"Reward: {self.last_episode_reward:+.1f} | "
                  f"Length: {self.last_episode_length}")

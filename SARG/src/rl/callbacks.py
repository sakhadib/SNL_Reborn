"""
Training Callbacks
Handles checkpointing, evaluation, and monitoring during training.
"""

from pathlib import Path
from typing import Dict, Any, Optional
from stable_baselines3.common.callbacks import BaseCallback
from rich.console import Console
from rich.table import Table
from rich.live import Live
from rich.layout import Layout
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, BarColumn, TextColumn, TimeElapsedColumn
import sys

from src.rl.evaluator import Evaluator

console = Console()


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
            
            # Update trainer episode count
            if self.trainer:
                self.trainer.total_episodes += 1
                self.trainer.phase_episodes += 1
            
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
        from src.rl.environment import SARGEnv
        
        # Create temporary env for agent
        temp_env = SARGEnv(opponent=None, config=self.trainer.config if self.trainer else {})
        
        # Wrap model in RLAgent for evaluation
        agent = RLAgent(env=temp_env, config={})
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
    Callback for console logging with in-place updating rich display.
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
            log_freq: Update display every N timesteps
            trainer: CurriculumTrainer instance
            verbose: Verbosity level
        """
        super().__init__(verbose)
        self.log_freq = log_freq
        self.trainer = trainer
        
        self.episode_count = 0
        self.last_episode_reward = 0
        self.last_episode_length = 0
        self.recent_rewards = []
        self.recent_wins = []
        self.live: Optional[Live] = None
        self.steps_since_log = 0
        
    def _on_training_start(self) -> None:
        """Start the rich Live display."""
        if self.verbose > 0:
            self.live = Live(console=console, refresh_per_second=4, screen=False)
            self.live.start()
    
    def _on_training_end(self) -> None:
        """Stop the rich Live display."""
        if self.live:
            self.live.stop()
            self.live = None
    
    def _on_step(self) -> bool:
        """
        Called after each environment step.
        
        Returns:
            True to continue training
        """
        self.steps_since_log += 1
        
        # Check if episode just finished
        if self.locals.get('dones', [False])[0]:
            self.episode_count += 1
            
            # Update trainer episode count
            if self.trainer:
                self.trainer.total_episodes += 1
                self.trainer.phase_episodes += 1
            
            # Get episode info
            infos = self.locals.get('infos', [{}])
            if len(infos) > 0:
                self.last_episode_reward = infos[0].get('episode', {}).get('r', 0)
                self.last_episode_length = infos[0].get('episode', {}).get('l', 0)
                
                # Track wins
                won = self.last_episode_reward > 0
                self.recent_wins.append(won)
                self.recent_rewards.append(self.last_episode_reward)
                
                # Keep window size
                if len(self.recent_wins) > 1000:
                    self.recent_wins = self.recent_wins[-1000:]
                    self.recent_rewards = self.recent_rewards[-1000:]
                
                # Update trainer win rate
                if self.trainer and len(self.recent_wins) > 0:
                    self.trainer.recent_win_rate = sum(self.recent_wins) / len(self.recent_wins)
                    if self.trainer.recent_win_rate > self.trainer.best_win_rate:
                        self.trainer.best_win_rate = self.trainer.recent_win_rate
        
        # Update display periodically
        if self.steps_since_log >= self.log_freq and self.verbose > 0:
            self._update_display()
            self.steps_since_log = 0
        
        return True
    
    def _update_display(self):
        """Update the live display with current progress."""
        if not self.live or not self.trainer:
            return
        
        if len(self.recent_wins) < 10:
            # Not enough data yet
            return
        
        recent_wr = sum(self.recent_wins[-100:]) / len(self.recent_wins[-100:]) if len(self.recent_wins) >= 100 else sum(self.recent_wins) / len(self.recent_wins)
        avg_reward = sum(self.recent_rewards[-100:]) / len(self.recent_rewards[-100:]) if len(self.recent_rewards) >= 100 else sum(self.recent_rewards) / len(self.recent_rewards)
        
        # Create table
        table = Table(show_header=True, header_style="bold magenta", title=f"SARG RL Training - Phase {self.trainer.current_phase}")
        table.add_column("Episode", style="cyan", justify="right")
        table.add_column("Win Rate", style="yellow", justify="right")
        table.add_column("Best WR", style="green", justify="right")
        table.add_column("Avg Reward", style="blue", justify="right")
        table.add_column("Ep Length", style="white", justify="right")
        
        table.add_row(
            f"{self.trainer.total_episodes:,}",
            f"{recent_wr:.1%}",
            f"{self.trainer.best_win_rate:.1%}",
            f"{avg_reward:+.1f}",
            f"{self.last_episode_length:.0f}"
        )
        
        self.live.update(table)

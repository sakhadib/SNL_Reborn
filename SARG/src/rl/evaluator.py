"""
Evaluator for RL Agent
Tests agent against heuristic baselines and computes metrics.
"""

import json
import random
from pathlib import Path
from typing import Dict, Any, List, Tuple
from datetime import datetime

from src.rl.environment import SARGEnv
from src.rl.rl_agent import RLAgent
from src.agents import AGENT_REGISTRY
from src.engine import Player
from src.evaluation.elo_rating import EloRating, GameResult


class Evaluator:
    """
    Evaluates RL agent against heuristic opponents.
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize evaluator.
        
        Args:
            config: Evaluation configuration
        """
        self.config = config
        self.games_per_opponent = config.get("eval_games_per_opponent", 100)
        self.alternating_start = config.get("eval_alternating_start", True)
        self.eval_dir = Path(config.get("eval_dir", "data/rl_evaluation"))
        self.eval_dir.mkdir(parents=True, exist_ok=True)
    
    def evaluate(
        self,
        agent: RLAgent,
        opponents: List[str] = None,
        episode_num: int = 0,
        phase: int = 1
    ) -> Dict[str, Any]:
        """
        Evaluate agent against opponents.
        
        Args:
            agent: RL agent to evaluate
            opponents: List of opponent IDs (if None, uses all heuristics)
            episode_num: Current training episode number
            phase: Current training phase
            
        Returns:
            Evaluation results dictionary
        """
        if opponents is None:
            opponents = list(AGENT_REGISTRY.keys())
        
        print(f"\n{'='*70}")
        print(f"EVALUATION at Episode {episode_num:,} (Phase {phase})")
        print(f"{'='*70}")
        print(f"Testing against {len(opponents)} opponents...")
        print()
        
        results = {}
        total_wins = 0
        total_games = 0
        
        for opponent_id in opponents:
            wins, losses, avg_margin = self._evaluate_opponent(agent, opponent_id)
            
            results[opponent_id] = {
                "wins": wins,
                "losses": losses,
                "win_rate": wins / (wins + losses) if (wins + losses) > 0 else 0.0,
                "avg_margin": avg_margin
            }
            
            total_wins += wins
            total_games += wins + losses
            
            print(f"  {opponent_id:20s}: {wins:3d}W {losses:3d}L ({results[opponent_id]['win_rate']:.1%}) avg_margin={avg_margin:.1f}")
        
        overall_win_rate = total_wins / total_games if total_games > 0 else 0.0
        
        # Calculate estimated Elo rating (starting from 1500)
        elo_system = EloRating(k_factor=24.0, alpha=0.75)
        rl_rating = 1500.0
        
        for opponent_id, result in results.items():
            opponent_rating = 1500.0  # Assume baseline rating
            wins = result["wins"]
            losses = result["losses"]
            avg_margin = result["avg_margin"]
            
            # Update Elo based on each game result (approximate using average margin)
            for _ in range(wins):
                game_result = GameResult(
                    winner_id="rl_agent",
                    loser_id=opponent_id,
                    loser_final_position=int(100 - avg_margin),
                    num_turns=0
                )
                rl_rating, opponent_rating = elo_system.update_ratings(rl_rating, opponent_rating, game_result)
                
            for _ in range(losses):
                game_result = GameResult(
                    winner_id=opponent_id,
                    loser_id="rl_agent",
                    loser_final_position=int(100 - avg_margin),
                    num_turns=0
                )
                opponent_rating, rl_rating = elo_system.update_ratings(opponent_rating, rl_rating, game_result)
        
        print()
        print(f"Overall: {total_wins}/{total_games} ({overall_win_rate:.1%})")
        print(f"Estimated Elo Rating: {rl_rating:.0f}")
        print(f"{'='*70}\n")
        
        # Compile evaluation report
        eval_report = {
            "episode": episode_num,
            "phase": phase,
            "timestamp": datetime.now().isoformat(),
            "results": results,
            "overall_win_rate": overall_win_rate,
            "total_wins": total_wins,
            "total_games": total_games,
            "estimated_elo": rl_rating,
        }
        
        # Save evaluation report
        self._save_evaluation(eval_report, episode_num)
        
        return eval_report
    
    def _evaluate_opponent(
        self,
        agent: RLAgent,
        opponent_id: str
    ) -> Tuple[int, int, float]:
        """
        Evaluate agent against single opponent.
        
        Args:
            agent: RL agent
            opponent_id: Opponent ID
            
        Returns:
            Tuple of (wins, losses, avg_margin)
        """
        wins = 0
        losses = 0
        margins = []
        
        # Create environment with this opponent
        env = SARGEnv(opponent_id=opponent_id, config=self.config)
        
        for game_num in range(self.games_per_opponent):
            # Alternate starting player
            if self.alternating_start:
                rl_player = Player.A if game_num % 2 == 0 else Player.B
            else:
                rl_player = Player.A
            
            # Play game
            obs, info = env.reset(options={'rl_player': rl_player})
            done = False
            
            while not done:
                action_mask = env.action_masks()
                action, _ = agent.predict(obs, action_mask, deterministic=True)
                obs, reward, terminated, truncated, info = env.step(action)
                done = terminated or truncated
            
            # Record result
            if reward > 0:
                wins += 1
                loser_pos = env.state.get_loser_final_position()
                margin = 100 - loser_pos
                margins.append(margin)
            else:
                losses += 1
                loser_pos = env.state.get_loser_final_position()
                margin = 100 - loser_pos
                margins.append(-margin)  # Negative margin for losses
        
        avg_margin = sum(margins) / len(margins) if margins else 0.0
        
        return wins, losses, avg_margin
    
    def _save_evaluation(self, eval_report: Dict[str, Any], episode_num: int):
        """Save evaluation report to JSON."""
        filename = f"evaluation_episode_{episode_num:08d}.json"
        filepath = self.eval_dir / filename
        
        with open(filepath, 'w') as f:
            json.dump(eval_report, f, indent=2)

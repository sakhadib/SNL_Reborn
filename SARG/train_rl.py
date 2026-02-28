#!/usr/bin/env python3
"""
RL Training CLI
Train SARG RL-V1 agent with 4-phase curriculum.
"""

import argparse
import sys
from pathlib import Path

from src.rl.config import get_config, create_directories
from src.rl.trainer import CurriculumTrainer
from src.rl.evaluator import Evaluator
from src.rl.callbacks import CheckpointCallback, EvaluationCallback, ConsoleCallback


def main():
    parser = argparse.ArgumentParser(
        description='Train SARG RL-V1 Agent with Curriculum Learning'
    )
    
    # Training control
    parser.add_argument(
        '--episodes',
        type=int,
        default=None,
        help='Total episodes to train (overrides config)'
    )
    parser.add_argument(
        '--phase',
        type=int,
        default=1,
        choices=[1, 2, 3, 4],
        help='Starting phase (1-4)'
    )
    parser.add_argument(
        '--resume',
        action='store_true',
        help='Resume from latest checkpoint'
    )
    
    # Hyperparameter overrides
    parser.add_argument(
        '--lr',
        type=float,
        default=None,
        help='Learning rate override'
    )
    parser.add_argument(
        '--batch-size',
        type=int,
        default=None,
        help='Batch size override'
    )
    parser.add_argument(
        '--n-steps',
        type=int,
        default=None,
        help='Rollout buffer size override'
    )
    
    # Evaluation and checkpointing
    parser.add_argument(
        '--checkpoint-freq',
        type=int,
        default=None,
        help='Checkpoint frequency (episodes)'
    )
    parser.add_argument(
        '--eval-freq',
        type=int,
        default=None,
        help='Evaluation frequency (episodes)'
    )
    parser.add_argument(
        '--no-eval',
        action='store_true',
        help='Disable periodic evaluation'
    )
    
    # Logging
    parser.add_argument(
        '--log-freq',
        type=int,
        default=100,
        help='Console log frequency (episodes)'
    )
    parser.add_argument(
        '--quiet',
        action='store_true',
        help='Minimal console output'
    )
    
    # Paths
    parser.add_argument(
        '--checkpoint-dir',
        type=str,
        default='data/rl_checkpoints',
        help='Checkpoint directory'
    )
    parser.add_argument(
        '--log-dir',
        type=str,
        default='data/rl_logs',
        help='TensorBoard log directory'
    )
    
    # Random seed
    parser.add_argument(
        '--seed',
        type=int,
        default=42,
        help='Random seed'
    )
    
    args = parser.parse_args()
    
    # Build configuration with overrides
    config_overrides = {
        'seed': args.seed,
        'checkpoint_dir': args.checkpoint_dir,
        'log_dir': args.log_dir,
        'verbose': 0 if args.quiet else 1,
    }
    
    if args.lr is not None:
        config_overrides['learning_rate'] = args.lr
    if args.batch_size is not None:
        config_overrides['batch_size'] = args.batch_size
    if args.n_steps is not None:
        config_overrides['n_steps'] = args.n_steps
    if args.checkpoint_freq is not None:
        config_overrides['checkpoint_freq'] = args.checkpoint_freq
    if args.eval_freq is not None:
        config_overrides['eval_freq'] = args.eval_freq
    if args.log_freq is not None:
        config_overrides['console_log_freq'] = args.log_freq
    
    config = get_config(config_overrides)
    
    # Create directories
    create_directories(config)
    
    # Print header
    if not args.quiet:
        print("\n" + "="*70)
        print("SARG RL-V1 TRAINING")
        print("="*70)
        print(f"Starting phase: {args.phase}")
        print(f"Resume: {args.resume}")
        print(f"Seed: {args.seed}")
        print(f"Learning rate: {config['learning_rate']}")
        print(f"Batch size: {config['batch_size']}")
        print(f"Checkpoint freq: {config['checkpoint_freq']:,} episodes")
        if not args.no_eval:
            print(f"Evaluation freq: {config['eval_freq']:,} episodes")
        print("="*70 + "\n")
    
    # Initialize trainer
    trainer = CurriculumTrainer(config)
    trainer.initialize_training(resume=args.resume)
    
    # If resuming, potentially start from later phase
    if args.resume and trainer.current_phase > args.phase:
        start_phase = trainer.current_phase
    else:
        start_phase = args.phase
    
    # Create evaluator
    evaluator = Evaluator(config)
    
    # Setup callbacks
    callbacks = [
        CheckpointCallback(
            checkpoint_freq=config['checkpoint_freq'],
            checkpoint_dir=config['checkpoint_dir'],
            save_best=config.get('save_best', True),
            trainer=trainer,
            verbose=0 if args.quiet else 1
        ),
        ConsoleCallback(
            log_freq=config['console_log_freq'],
            trainer=trainer,
            verbose=0 if args.quiet else 1
        )
    ]
    
    if not args.no_eval:
        callbacks.append(
            EvaluationCallback(
                eval_freq=config['eval_freq'],
                evaluator=evaluator,
                trainer=trainer,
                verbose=0 if args.quiet else 1
            )
        )
    
    try:
        # Train curriculum
        if not args.quiet:
            print("Starting curriculum training...\n")
        
        # For now, train one phase at a time with PPO.learn()
        # Full curriculum integration requires custom training loop
        
        # Simple pilot: Train Phase 1 for specified episodes
        if args.episodes:
            total_timesteps = args.episodes
        else:
            # Use phase 1 default
            total_timesteps = config['phase_1_min_episodes']
        
        if not args.quiet:
            print(f"Training Phase {start_phase} for {total_timesteps:,} episodes...")
        
        # Train
        trainer.agent.model.learn(
            total_timesteps=total_timesteps,
            callback=callbacks,
            progress_bar=not args.quiet
        )
        
        # Save final checkpoint
        final_path = Path(config['checkpoint_dir']) / "rl_v1_final.zip"
        trainer.agent.save(final_path)
        
        if not args.quiet:
            print(f"\n✓ Training complete!")
            print(f"Final model saved to {final_path}")
            
            summary = trainer.get_training_summary()
            print(f"\nTraining Summary:")
            print(f"  Total episodes: {summary['total_episodes']:,}")
            print(f"  Final win rate: {summary['recent_win_rate']:.1%}")
            print(f"  Best win rate: {summary['best_win_rate']:.1%}")
        
        return 0
        
    except KeyboardInterrupt:
        print("\n\nTraining interrupted by user")
        
        # Save emergency checkpoint
        emergency_path = Path(config['checkpoint_dir']) / "rl_v1_interrupted.zip"
        trainer.agent.save(emergency_path)
        print(f"Emergency checkpoint saved to {emergency_path}")
        
        return 1
        
    except Exception as e:
        print(f"\nError during training: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())

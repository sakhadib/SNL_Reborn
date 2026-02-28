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
        # Train with full curriculum and automatic phase progression
        if not args.quiet:
            print("Starting curriculum training with automatic phase progression...\n")
        
        # Train all phases from start_phase
        for phase in range(start_phase, 5):
            trainer.current_phase = phase
            trainer.phase_episodes = 0
            
            # Get phase configuration
            from src.rl.config import get_phase_config
            phase_config = get_phase_config(phase, config)
            
            # Update environment opponent for new phase
            trainer._update_opponent_for_phase(phase)
            trainer.agent.env.set_opponent(opponent_id=trainer._get_current_opponent(phase_config))
            
            # Determine episode limits
            if args.episodes and phase == start_phase:
                # User override for first phase only
                max_episodes = args.episodes
            else:
                max_episodes = phase_config['max_episodes']
            
            min_episodes = phase_config['min_episodes']
            target_wr = phase_config.get('target_wr', None)
            
            if not args.quiet:
                print(f"\n{'='*70}")
                print(f"PHASE {phase}: {trainer._get_phase_name(phase)}")
                print(f"{'='*70}")
                print(f"Min episodes: {min_episodes:,}")
                print(f"Max episodes: {max_episodes:,}")
                if target_wr:
                    print(f"Target win rate: {target_wr:.1%}")
                print()
            
            # Train this phase
            phase_start_episode = trainer.total_episodes
            episodes_trained = 0
            
            while episodes_trained < max_episodes:
                # Train in chunks of 50k timesteps
                chunk_timesteps = min(50000, (max_episodes - episodes_trained) * 50)
                
                trainer.agent.model.learn(
                    total_timesteps=chunk_timesteps,
                    callback=callbacks,
                    reset_num_timesteps=False,
                    progress_bar=False  # Disable SB3 progress bar (we use custom console callback)
                )
                
                episodes_trained = trainer.total_episodes - phase_start_episode
                
                # Check phase completion criteria
                if target_wr and episodes_trained >= min_episodes:
                    if trainer.recent_win_rate >= target_wr:
                        if not args.quiet:
                            print(f"\n✓ Phase {phase} target achieved!")
                            print(f"  Episodes: {episodes_trained:,}")
                            print(f"  Win rate: {trainer.recent_win_rate:.1%}")
                        break
                
                # Update opponent for variety (Phase 2-4)
                if phase >= 2:
                    trainer.agent.env.set_opponent(opponent_id=trainer._get_current_opponent(phase_config))
            
            # Save phase completion
            trainer.phase_win_rates[phase] = trainer.recent_win_rate
            trainer._save_training_state()
            
            # Save phase checkpoint
            phase_path = Path(config['checkpoint_dir']) / f"rl_v1_phase{phase}_complete.zip"
            trainer.agent.save(phase_path)
            
            if not args.quiet:
                print(f"\n{'='*70}")
                print(f"Phase {phase} Complete!")
                print(f"{'='*70}")
                print(f"Episodes trained: {episodes_trained:,}")
                print(f"Final win rate: {trainer.recent_win_rate:.1%}")
                print(f"Checkpoint: {phase_path}")
                print()
            
            # Check if should continue
            if target_wr and trainer.recent_win_rate < target_wr:
                print(f"\nWarning: Target win rate not achieved, but max episodes reached.")
                if phase < 4:
                    response = input("Continue to next phase? (y/n): ")
                    if response.lower() != 'y':
                        break
        
        # Save final checkpoint
        final_path = Path(config['checkpoint_dir']) / "rl_v1_final.zip"
        trainer.agent.save(final_path)
        
        if not args.quiet:
            print(f"\n{'='*70}")
            print("✓ TRAINING COMPLETE!")
            print(f"{'='*70}")
            
            summary = trainer.get_training_summary()
            print(f"\nFinal Summary:")
            print(f"  Total episodes: {summary['total_episodes']:,}")
            print(f"  Final phase: {summary['current_phase']}")
            print(f"  Final win rate: {summary['recent_win_rate']:.1%}")
            print(f"  Best win rate: {summary['best_win_rate']:.1%}")
            print(f"\nPhase Win Rates:")
            for p, wr in summary['phase_win_rates'].items():
                print(f"  Phase {p}: {wr:.1%}")
            print(f"\nFinal model: {final_path}")
        
        return 0
        
    except KeyboardInterrupt:
        print("\n\nTraining interrupted by user")
        
        # Save training state first
        trainer._save_training_state()
        print(f"Training state saved to {trainer.training_state_path}")
        
        # Save emergency checkpoint
        emergency_path = Path(config['checkpoint_dir']) / "rl_v1_interrupted.zip"
        trainer.agent.save(emergency_path)
        print(f"Emergency checkpoint saved to {emergency_path}")
        
        print("\n✓ Safe to push to GitHub. Your teammates can resume with:")
        print(f"  python3 train_rl.py --resume --checkpoint-freq {args.checkpoint_freq} --eval-freq {args.eval_freq} --log-freq {args.log_freq} --seed {args.seed}")
        
        return 1
        
    except Exception as e:
        print(f"\nError during training: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())

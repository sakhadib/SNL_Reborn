#!/usr/bin/env python3
"""
Tournament Runner - Round-robin tournament with persistent Elo ratings.

Features:
- Round-robin format (each pair plays N games)
- Alternating starting player
- Margin-scaled Elo rating updates
- Persistent ratings across tournaments
- Game storage in binary format
- Detailed statistics and reporting

Usage:
    python3 tournament.py --agents maxim minim exactor --games 100
    python3 tournament.py --agents-file agents.txt --games 500 --save-games
    python3 tournament.py --all-agents --games 50
"""

import argparse
import random
from pathlib import Path
from typing import List, Tuple
from datetime import datetime
import sys

from src.engine import GameEngine, GameState, Player
from src.agents import AGENT_REGISTRY
from src.evaluation import EloRating, GameResult, RatingTracker, TournamentStats
from src.storage import GameWriter


def play_game(
    p1_agent,
    p2_agent,
    engine: GameEngine,
    seed: int = None
) -> Tuple[Player, int, int]:
    """
    Play a single game between two agents.
    
    Args:
        p1_agent: Player A agent
        p2_agent: Player B agent
        engine: Game engine (with replay tracking)
        seed: Random seed
        
    Returns:
        Tuple of (winner, loser_final_position, num_turns)
    """
    if seed is not None:
        random.seed(seed)
    
    # Reset replay for new game
    state = GameState.initial_state(engine.board)
    engine.reset_replay(state)
    
    turn = 0
    
    while not state.is_terminal():
        turn += 1
        current_player = state.current_player
        
        # Roll dice
        dice1 = random.randint(1, 6)
        dice2 = random.randint(1, 6)
        
        # Get action
        agent = p1_agent if current_player == Player.A else p2_agent
        action = agent.choose_action(engine, state, current_player, dice1, dice2)
        
        # Execute move
        state, move_info = engine.execute_move(state, dice1, dice2, action)
    
    # Get result
    winner = state.get_winner()
    loser_pos = state.get_loser_final_position()
    
    return winner, loser_pos, turn


def run_matchup(
    agent1_id: str,
    agent2_id: str,
    games_per_matchup: int,
    elo_system: EloRating,
    rating_tracker: RatingTracker,
    stats: TournamentStats,
    game_writer: GameWriter = None,
    verbose: bool = False
) -> int:
    """
    Run all games for a specific matchup with alternating starting player.
    
    Args:
        agent1_id: First agent ID
        agent2_id: Second agent ID
        games_per_matchup: Number of games to play
        elo_system: Elo rating system
        rating_tracker: Rating tracker
        stats: Tournament statistics
        game_writer: Optional game writer for storage
        verbose: Print game-by-game results
        
    Returns:
        Number of games played
    """
    # Create agents
    agent1 = AGENT_REGISTRY[agent1_id]()
    agent2 = AGENT_REGISTRY[agent2_id]()
    
    games_played = 0
    
    if verbose:
        print(f"\n  {agent1_id} vs {agent2_id}: ", end="", flush=True)
    
    for game_num in range(games_per_matchup):
        # Create fresh engine for each game
        engine = GameEngine()
        
        # Alternate starting player
        if game_num % 2 == 0:
            # Agent1 as Player A
            p1_agent, p2_agent = agent1, agent2
            p1_id, p2_id = agent1_id, agent2_id
        else:
            # Agent2 as Player A
            p1_agent, p2_agent = agent2, agent1
            p1_id, p2_id = agent2_id, agent1_id
        
        # Play game
        winner_player, loser_pos, turns = play_game(p1_agent, p2_agent, engine)
        
        # Determine winner/loser IDs
        winner_id = p1_id if winner_player == Player.A else p2_id
        loser_id = p2_id if winner_player == Player.A else p1_id
        
        # Calculate margin
        margin = 100 - loser_pos
        
        # Create game result
        result = GameResult(
            winner_id=winner_id,
            loser_id=loser_id,
            loser_final_position=loser_pos,
            num_turns=turns
        )
        
        # Update Elo ratings
        winner_rating = rating_tracker.get_rating(winner_id)
        loser_rating = rating_tracker.get_rating(loser_id)
        
        new_winner_rating, new_loser_rating = elo_system.update_ratings(
            winner_rating, loser_rating, result
        )
        
        # Update tracker
        rating_tracker.update_rating(winner_id, new_winner_rating, True, margin)
        rating_tracker.update_rating(loser_id, new_loser_rating, False, margin)
        
        # Record statistics
        stats.record_game(agent1_id, agent2_id, winner_id, margin, turns)
        
        # Save game if writer provided
        if game_writer:
            # Use small sequential IDs for agents (0-254)
            p1_agent_id = list(AGENT_REGISTRY.keys()).index(p1_id) if p1_id in AGENT_REGISTRY else 0
            p2_agent_id = list(AGENT_REGISTRY.keys()).index(p2_id) if p2_id in AGENT_REGISTRY else 1
            game_writer.write_game(
                engine.get_replay(),
                player_a_id=p1_agent_id,
                player_b_id=p2_agent_id
            )
        
        games_played += 1
        
        if verbose and (game_num + 1) % 10 == 0:
            print(f"{game_num + 1}", end=" ", flush=True)
    
    if verbose:
        print("✓")
    
    return games_played


def run_tournament(
    agent_ids: List[str],
    games_per_matchup: int,
    rating_file: Path,
    k_factor: float = 24.0,
    alpha: float = 0.75,
    save_games: bool = False,
    games_file: Path = None,
    verbose: bool = True,
    seed_base: int = None
) -> TournamentStats:
    """
    Run a complete round-robin tournament.
    
    Args:
        agent_ids: List of agent IDs to compete
        games_per_matchup: Games per matchup
        rating_file: Path to persistent rating file
        k_factor: Elo K-factor
        alpha: Margin sensitivity
        save_games: Whether to save games to binary storage
        games_file: Path to games storage file
        verbose: Print progress
        seed_base: Base seed for reproducibility
        
    Returns:
        TournamentStats object with results
    """
    if seed_base is not None:
        random.seed(seed_base)
    
    # Initialize systems
    elo_system = EloRating(k_factor=k_factor, alpha=alpha)
    rating_tracker = RatingTracker(rating_file)
    stats = TournamentStats()
    
    # Initialize game writer if saving
    game_writer = None
    if save_games and games_file:
        game_writer = GameWriter(games_file)
    
    # Print tournament header
    if verbose:
        print("\n" + "="*70)
        print("TOURNAMENT START")
        print("="*70)
        print(f"\nAgents: {', '.join(agent_ids)}")
        print(f"Games per matchup: {games_per_matchup}")
        print(f"Total matchups: {len(agent_ids) * (len(agent_ids) - 1) // 2}")
        print(f"Total games: {games_per_matchup * len(agent_ids) * (len(agent_ids) - 1) // 2}")
        print(f"K-factor: {k_factor}, Alpha: {alpha}")
        print(f"Max rating swing: {elo_system.max_rating_swing():.1f}")
        
        print("\n" + "-"*70)
        print("INITIAL RATINGS")
        print("-"*70)
        for agent_id in agent_ids:
            rating = rating_tracker.get_rating(agent_id)
            print(f"  {agent_id}: {rating:.1f}")
    
    # Snapshot initial ratings
    stats.snapshot_ratings(rating_tracker.get_all_ratings())
    
    # Run all matchups
    if verbose:
        print("\n" + "-"*70)
        print("RUNNING GAMES")
        print("-"*70)
    
    total_games = 0
    for i, agent1_id in enumerate(agent_ids):
        for agent2_id in agent_ids[i+1:]:
            games = run_matchup(
                agent1_id, agent2_id,
                games_per_matchup,
                elo_system, rating_tracker, stats,
                game_writer, verbose
            )
            total_games += games
    
    # Snapshot final ratings
    stats.snapshot_ratings(rating_tracker.get_all_ratings())
    
    # Save ratings
    rating_tracker.save()
    
    if verbose:
        print(f"\nTotal games played: {total_games}")
    
    return stats, rating_tracker


def print_results(stats: TournamentStats, rating_tracker: RatingTracker):
    """Print tournament results."""
    print("\n" + "="*70)
    print("TOURNAMENT RESULTS")
    print("="*70)
    
    # Leaderboard
    print("\n" + "-"*70)
    print("FINAL LEADERBOARD")
    print("-"*70)
    print(f"{'Rank':<6} {'Agent':<20} {'Rating':<10} {'Games':<8} {'W-L':<12} {'Win%':<8}")
    print("-"*70)
    
    leaderboard = rating_tracker.get_leaderboard()
    for rank, (agent_id, rating, games, wins, losses, win_rate) in enumerate(leaderboard, 1):
        print(f"{rank:<6} {agent_id:<20} {rating:>8.1f}  {games:<8} {wins}-{losses:<8} {win_rate:>6.1%}")
    
    # Agent summaries
    print("\n" + "-"*70)
    print("AGENT SUMMARIES")
    print("-"*70)
    
    for agent_id, rating, games, wins, losses, win_rate in leaderboard:
        agent_stats = stats.get_agent_summary(agent_id)
        print(f"\n{agent_id}:")
        print(f"  Rating: {rating:.1f}")
        print(f"  Games: {games}, Wins: {wins}, Losses: {losses}")
        print(f"  Win Rate: {win_rate:.1%}")
        print(f"  Avg Margin: {agent_stats['avg_margin']:.1f}")
        print(f"  Max Margin: {agent_stats['max_margin']}")


def main():
    parser = argparse.ArgumentParser(
        description='SARG Tournament - Round-robin with persistent Elo ratings'
    )
    
    # Agent selection
    agent_group = parser.add_mutually_exclusive_group(required=True)
    agent_group.add_argument(
        '--agents',
        nargs='+',
        help=f'Agent IDs to compete: {", ".join(AGENT_REGISTRY.keys())}'
    )
    agent_group.add_argument(
        '--all-agents',
        action='store_true',
        help='Include all available agents'
    )
    agent_group.add_argument(
        '--agents-file',
        type=Path,
        help='File with agent IDs (one per line)'
    )
    
    # Tournament parameters
    parser.add_argument(
        '--games',
        type=int,
        default=100,
        help='Games per matchup (default: 100)'
    )
    parser.add_argument(
        '--k-factor',
        type=float,
        default=24.0,
        help='Elo K-factor (default: 24.0)'
    )
    parser.add_argument(
        '--alpha',
        type=float,
        default=0.75,
        help='Margin sensitivity (default: 0.75)'
    )
    
    # Storage
    parser.add_argument(
        '--rating-file',
        type=Path,
        default=Path('data/ratings.json'),
        help='Path to persistent rating file (default: data/ratings.json)'
    )
    parser.add_argument(
        '--save-games',
        action='store_true',
        help='Save all games to binary storage'
    )
    parser.add_argument(
        '--games-file',
        type=Path,
        default=Path('data/games/tournament.bin'),
        help='Path to games storage file (default: data/games/tournament.bin)'
    )
    
    # Other options
    parser.add_argument(
        '--seed',
        type=int,
        help='Random seed for reproducibility'
    )
    parser.add_argument(
        '--quiet',
        action='store_true',
        help='Minimize output'
    )
    
    args = parser.parse_args()
    
    # Determine agent list
    if args.all_agents:
        agent_ids = sorted(AGENT_REGISTRY.keys())
    elif args.agents_file:
        with open(args.agents_file) as f:
            agent_ids = [line.strip() for line in f if line.strip()]
    else:
        agent_ids = args.agents
    
    # Validate agents
    invalid_agents = [a for a in agent_ids if a not in AGENT_REGISTRY]
    if invalid_agents:
        print(f"Error: Unknown agents: {', '.join(invalid_agents)}")
        print(f"Available: {', '.join(AGENT_REGISTRY.keys())}")
        return 1
    
    if len(agent_ids) < 2:
        print("Error: Need at least 2 agents for a tournament")
        return 1
    
    # Run tournament
    try:
        stats, rating_tracker = run_tournament(
            agent_ids=agent_ids,
            games_per_matchup=args.games,
            rating_file=args.rating_file,
            k_factor=args.k_factor,
            alpha=args.alpha,
            save_games=args.save_games,
            games_file=args.games_file,
            verbose=not args.quiet,
            seed_base=args.seed
        )
        
        # Print results
        if not args.quiet:
            print_results(stats, rating_tracker)
        
        return 0
        
    except KeyboardInterrupt:
        print("\n\nTournament interrupted by user")
        return 1
    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())

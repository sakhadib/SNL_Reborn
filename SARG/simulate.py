#!/usr/bin/env python3
"""
Tournament Simulator - Run multiple tournaments with persistent Elo ratings.

Each tournament is a complete round-robin where ratings carry forward from
tournament to tournament, simulating a continuous competitive season.

Usage:
    python3 simulate.py --n 10 --agents maxim minim exactor
    python3 simulate.py --n 5 --all-agents --games 50
    python3 simulate.py --n 20 --agents-file agents.txt --games 100 --save-games
"""

import argparse
import sys
from pathlib import Path
from datetime import datetime
from typing import List
import uuid
from tqdm import tqdm

from src.engine import GameEngine, GameState, Player
from src.agents import AGENT_REGISTRY
from src.evaluation import EloRating, GameResult, RatingTracker, TournamentStats
from src.storage import GameWriter
from tournament import run_tournament, print_results


def print_simulation_header(
    num_tournaments: int,
    agent_ids: List[str],
    games_per_matchup: int,
    rating_file: Path
):
    """Print simulation header with parameters."""
    print("\n" + "="*70)
    print("TOURNAMENT SIMULATION")
    print("="*70)
    print(f"\nNumber of tournaments: {num_tournaments}")
    print(f"Agents: {', '.join(agent_ids)}")
    print(f"Games per matchup per tournament: {games_per_matchup}")
    print(f"Matchups per tournament: {len(agent_ids) * (len(agent_ids) - 1) // 2}")
    print(f"Games per tournament: {games_per_matchup * len(agent_ids) * (len(agent_ids) - 1) // 2}")
    print(f"Total games across all tournaments: {num_tournaments * games_per_matchup * len(agent_ids) * (len(agent_ids) - 1) // 2}")
    print(f"\nRating file: {rating_file}")
    print(f"Ratings persist across all tournaments")


def print_tournament_separator(tournament_num: int, total: int):
    """Print separator between tournaments."""
    print("\n" + "="*70)
    print(f"TOURNAMENT {tournament_num}/{total}")
    print("="*70)


def print_simulation_summary(
    num_tournaments: int,
    rating_tracker: RatingTracker,
    initial_ratings: dict,
    rating_history: List[dict]
):
    """Print final simulation summary with rating progressions."""
    print("\n" + "="*70)
    print("SIMULATION COMPLETE")
    print("="*70)
    
    print(f"\nTotal tournaments completed: {num_tournaments}")
    
    # Final leaderboard
    print("\n" + "-"*70)
    print("FINAL LEADERBOARD")
    print("-"*70)
    print(f"{'Rank':<6} {'Agent':<20} {'Rating':<10} {'Change':<10} {'Games':<8} {'W-L':<12} {'Win%':<8}")
    print("-"*70)
    
    leaderboard = rating_tracker.get_leaderboard()
    for rank, (agent_id, rating, games, wins, losses, win_rate) in enumerate(leaderboard, 1):
        initial = initial_ratings.get(agent_id, 1500.0)
        change = rating - initial
        change_str = f"+{change:.1f}" if change >= 0 else f"{change:.1f}"
        print(f"{rank:<6} {agent_id:<20} {rating:>8.1f}  {change_str:>8}  {games:<8} {wins}-{losses:<8} {win_rate:>6.1%}")
    
    # Rating progression
    print("\n" + "-"*70)
    print("RATING PROGRESSION")
    print("-"*70)
    
    if rating_history and len(rating_history) > 1:
        # Get all agents
        all_agents = sorted(set(agent for snapshot in rating_history for agent in snapshot.keys()))
        
        print(f"\n{'Agent':<20}", end="")
        for i in range(min(num_tournaments + 1, len(rating_history))):
            if i == 0:
                print(f"{'Initial':<10}", end="")
            else:
                print(f"{'T' + str(i):<10}", end="")
        print()
        print("-"*70)
        
        for agent_id in all_agents:
            print(f"{agent_id:<20}", end="")
            for snapshot in rating_history[:num_tournaments + 1]:
                rating = snapshot.get(agent_id, 1500.0)
                print(f"{rating:>9.1f} ", end="")
            print()
    
    # Biggest gainers and losers
    print("\n" + "-"*70)
    print("RATING CHANGES")
    print("-"*70)
    
    changes = []
    for agent_id, rating, games, wins, losses, win_rate in leaderboard:
        initial = initial_ratings.get(agent_id, 1500.0)
        change = rating - initial
        changes.append((agent_id, change, rating))
    
    changes.sort(key=lambda x: x[1], reverse=True)
    
    print("\nBiggest Gainers:")
    for agent_id, change, final_rating in changes[:3]:
        print(f"  {agent_id}: +{change:.1f} (→ {final_rating:.1f})")
    
    print("\nBiggest Losers:")
    for agent_id, change, final_rating in changes[-3:]:
        print(f"  {agent_id}: {change:.1f} (→ {final_rating:.1f})")


def run_simulation(
    num_tournaments: int,
    agent_ids: List[str],
    games_per_matchup: int,
    rating_file: Path,
    k_factor: float = 24.0,
    alpha: float = 0.75,
    save_games: bool = False,
    games_dir: Path = None,
    verbose: bool = True,
    seed_base: int = None
):
    """
    Run multiple tournaments with persistent ratings.
    
    Args:
        num_tournaments: Number of tournaments to run
        agent_ids: List of agent IDs
        games_per_matchup: Games per matchup per tournament
        rating_file: Path to rating file
        k_factor: Elo K-factor
        alpha: Margin sensitivity
        save_games: Save games to storage
        games_dir: Directory for game files
        verbose: Print detailed output
        seed_base: Base random seed
    """
    # Print header
    if verbose:
        print_simulation_header(num_tournaments, agent_ids, games_per_matchup, rating_file)
    
    # Track rating history
    rating_tracker = RatingTracker(rating_file)
    initial_ratings = rating_tracker.get_all_ratings()
    rating_history = [initial_ratings.copy()]
     with progress bar
    tournaments_iterator = range(1, num_tournaments + 1)
    if not verbose:
        tournaments_iterator = tqdm(tournaments_iterator, desc="Tournaments", unit="tournament")
    
    for tournament_num in tournaments_iterator
    for tournament_num in range(1, num_tournaments + 1):
        if verbose:
            print_tournament_separator(tournament_num, num_tournaments)
        
        # Determine seed for this tournament
        tournament_seed = None
        if seed_base is not None:
            tournament_seed = seed_base + tournament_num
        
        # Determine games file if saving with unique naming
        games_file = None
        if save_games and games_dir:
            # Generate unique filename: timestamp + microseconds + UUID
            # Format: tournament_YYYYMMDD_HHMMSS_microseconds_uuid.bin
            # This ensures:
            # - Temporal ordering via timestamp prefix (sortable)
            # - Zero collision via UUID (even across machines/simultaneous runs)
            # - No conflicts when merging repos from 5 teammates
            now = datetime.now()
            timestamp = now.strftime("%Y%m%d_%H%M%S")
            microseconds = now.microsecond
            unique_id = str(uuid.uuid4())[:8]  # First 8 chars of UUID sufficient
            filename = f"tournament_{timestamp}_{microseconds:06d}_{unique_id}.bin"
            games_file = games_dir / filename
        
        # Run tournament
        stats, rating_tracker = run_tournament(
            agent_ids=agent_ids,
            games_per_matchup=games_per_matchup,
            rating_file=rating_file,
            k_factor=k_factor,
            alpha=alpha,
            save_games=save_games,
            games_file=games_file,
            verbose=verbose,
            seed_base=tournament_seed
        )
        
        # Save rating snapshot
        rating_history.append(rating_tracker.get_all_ratings().copy())
        
        # Print mini summary after each tournament
        if verbose and num_tournaments > 1:
        
        # Update progress bar with current top agent
        if not verbose and hasattr(tournaments_iterator, 'set_postfix'):
            top_agent = rating_tracker.get_leaderboard()[0]
            tournaments_iterator.set_postfix(leader=f"{top_agent[0]} ({top_agent[1]:.0f})")
            print(f"\nAfter Tournament {tournament_num}:")
            top_3 = rating_tracker.get_leaderboard()[:3]
            for rank, (agent_id, rating, games, wins, losses, win_rate) in enumerate(top_3, 1):
                print(f"  {rank}. {agent_id}: {rating:.1f}")
    
    # Print final summary
    if verbose:
        print_simulation_summary(num_tournaments, rating_tracker, initial_ratings, rating_history)
    
    return rating_tracker, rating_history


def main():
    parser = argparse.ArgumentParser(
        description='SARG Tournament Simulator - Run multiple tournaments with persistent ratings'
    )
    
    # Number of tournaments
    parser.add_argument(
        '--n',
        type=int,
        required=True,
        help='Number of tournaments to run'
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
        help='Games per matchup per tournament (default: 100)'
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
        '--games-dir',
        type=Path,
        default=Path('data/games'),
        help='Directory for game files (default: data/games/)'
    )
    
    # Other options
    parser.add_argument(
        '--seed',
        type=int,
        help='Base random seed for reproducibility'
    )
    parser.add_argument(
        '--quiet',
        action='store_true',
        help='Suppress detailed output, show progress bar instead'
    )
    
    args = parser.parse_args()
    
    # Validate number of tournaments
    if args.n < 1:
        print("Error: Number of tournaments must be at least 1")
        return 1
    
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
        print("Error: Need at least 2 agents for tournaments")
        return 1
    
    # Run simulation
    try:
        rating_tracker, rating_history = run_simulation(
            num_tournaments=args.n,
            agent_ids=agent_ids,
            games_per_matchup=args.games,
            rating_file=args.rating_file,
            k_factor=args.k_factor,
            alpha=args.alpha,
            save_games=args.save_games,
            games_dir=args.games_dir,
            verbose=not args.quiet,
            seed_base=args.seed
        )
        
        return 0
        
    except KeyboardInterrupt:
        print("\n\nSimulation interrupted by user")
        return 1
    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())

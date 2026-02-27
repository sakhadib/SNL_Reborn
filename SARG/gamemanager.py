#!/usr/bin/env python3
"""
Game Manager CLI - Run games between heuristic agents.

Usage:
    python3 gamemanager.py --p1 maxim --p2 minim
    python3 gamemanager.py --p1 hunter --p2 anti_capture --verbose
"""

import argparse
import random
from src.engine import GameEngine, Player, GameState
from src.agents import AGENT_REGISTRY


def pretty_print_state(engine, state, turn_num, p1_agent, p2_agent):
    """Pretty print current game state."""
    print(f"\n{'='*60}")
    print(f"TURN {turn_num}")
    print(f"{'='*60}")
    
    # Player A info
    pa_pos = state.get_player_position(Player.A)
    pa_stun = state.get_player_stun(Player.A)
    pa_immunity = state.get_player_immunity(Player.A)
    
    print(f"\n{p1_agent.name} (Player A):")
    print(f"  Position: {pa_pos}/100")
    if pa_stun > 0:
        print(f"  Status: STUNNED ({pa_stun} turns remaining)")
    elif pa_immunity > 0:
        print(f"  Status: IMMUNE ({pa_immunity} turns remaining)")
    else:
        print(f"  Status: Normal")
    
    # Player B info
    pb_pos = state.get_player_position(Player.B)
    pb_stun = state.get_player_stun(Player.B)
    pb_immunity = state.get_player_immunity(Player.B)
    
    print(f"\n{p2_agent.name} (Player B):")
    print(f"  Position: {pb_pos}/100")
    if pb_stun > 0:
        print(f"  Status: STUNNED ({pb_stun} turns remaining)")
    elif pb_immunity > 0:
        print(f"  Status: IMMUNE ({pb_immunity} turns remaining)")
    else:
        print(f"  Status: Normal")


def pretty_print_turn(player_name, player, dice1, dice2, action, state):
    """Pretty print turn action."""
    print(f"\n{player_name}'s turn:")
    print(f"  Dice rolled: {dice1}, {dice2}")
    
    if state.get_player_stun(player) > 0:
        print(f"  Action: STUNNED - Cannot move")
    elif action.name == "SKIP":
        print(f"  Action: SKIP - No legal moves")
    elif action.name == "CHOOSE_DIE_1":
        print(f"  Action: Chose die 1 ({dice1})")
    elif action.name == "CHOOSE_DIE_2":
        print(f"  Action: Chose die 2 ({dice2})")


def pretty_print_result(state, p1_agent, p2_agent, turn_num):
    """Pretty print game result."""
    print(f"\n{'='*60}")
    print(f"GAME OVER")
    print(f"{'='*60}")
    
    winner = state.get_winner()
    winner_name = p1_agent.name if winner == Player.A else p2_agent.name
    winner_player = "Player A" if winner == Player.A else "Player B"
    
    print(f"\n🏆 WINNER: {winner_name} ({winner_player})")
    print(f"\nGame Statistics:")
    print(f"  Total turns: {turn_num}")
    
    # Final positions
    pa_pos = state.get_player_position(Player.A)
    pb_pos = state.get_player_position(Player.B)
    
    print(f"\nFinal Positions:")
    print(f"  {p1_agent.name}: {pa_pos}/100")
    print(f"  {p2_agent.name}: {pb_pos}/100")


def play_game(p1_agent, p2_agent, verbose=False, seed=None):
    """Play a game between two agents."""
    if seed is not None:
        random.seed(seed)
    
    engine = GameEngine()
    state = GameState.initial_state(engine.board)
    
    turn_num = 0
    
    while not state.is_terminal():
        turn_num += 1
        current_player = state.current_player
        
        # Pretty print state at start of turn
        if verbose:
            pretty_print_state(engine, state, turn_num, p1_agent, p2_agent)
        
        # Roll dice
        dice1 = random.randint(1, 6)
        dice2 = random.randint(1, 6)
        
        # Get agent action
        agent = p1_agent if current_player == Player.A else p2_agent
        action = agent.choose_action(engine, state, current_player, dice1, dice2)
        
        # Pretty print action
        if verbose:
            player_name = p1_agent.name if current_player == Player.A else p2_agent.name
            pretty_print_turn(player_name, current_player, dice1, dice2, action, state)
        
        # Execute move
        state, move_info = engine.execute_move(state, dice1, dice2, action)
    
    # Game over
    pretty_print_result(state, p1_agent, p2_agent, turn_num)
    
    return state


def main():
    parser = argparse.ArgumentParser(description='SARG Game Manager - Run games between agents')
    parser.add_argument('--p1', type=str, required=True, 
                       help=f'Player 1 agent: {", ".join(AGENT_REGISTRY.keys())}')
    parser.add_argument('--p2', type=str, required=True,
                       help=f'Player 2 agent: {", ".join(AGENT_REGISTRY.keys())}')
    parser.add_argument('--verbose', '-v', action='store_true',
                       help='Show detailed turn-by-turn output')
    parser.add_argument('--seed', type=int, default=None,
                       help='Random seed for reproducibility')
    
    args = parser.parse_args()
    
    # Validate agents
    if args.p1.lower() not in AGENT_REGISTRY:
        print(f"Error: Unknown agent '{args.p1}'")
        print(f"Available agents: {', '.join(AGENT_REGISTRY.keys())}")
        return 1
    
    if args.p2.lower() not in AGENT_REGISTRY:
        print(f"Error: Unknown agent '{args.p2}'")
        print(f"Available agents: {', '.join(AGENT_REGISTRY.keys())}")
        return 1
    
    # Create agents
    p1_agent = AGENT_REGISTRY[args.p1.lower()]()
    p2_agent = AGENT_REGISTRY[args.p2.lower()]()
    
    # Print game header
    print(f"\n{'='*60}")
    print(f"SARG GAME - {p1_agent.name} vs {p2_agent.name}")
    print(f"{'='*60}")
    if args.seed is not None:
        print(f"Random seed: {args.seed}")
    
    # Play game
    final_state = play_game(p1_agent, p2_agent, verbose=args.verbose, seed=args.seed)
    
    return 0


if __name__ == "__main__":
    exit(main())

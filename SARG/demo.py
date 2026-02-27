"""
Demo script showing SARG game engine in action.
"""

import random
from src.engine import (
    GameEngine, GameState, GameReplay,
    Player, Action, CANONICAL_BOARD
)


def random_agent_move(state, dice1, dice2):
    """Simple random agent that picks legal actions randomly."""
    engine = GameEngine()
    legal_actions = engine.get_legal_actions(state, dice1, dice2)
    return random.choice(legal_actions)


def demo_simple_game():
    """Demonstrate a simple game."""
    print("="*70)
    print("SARG GAME ENGINE DEMONSTRATION")
    print("="*70)
    print()
    
    # Show board info
    CANONICAL_BOARD.print_board_info()
    
    # Initialize game
    engine = GameEngine()
    state = GameState.initial_state()
    replay = GameReplay(initial_state=state)
    
    print("\nStarting game...")
    print()
    
    state.pretty_print()
    
    # Play game with random moves
    move_count = 0
    max_moves = 100
    
    while not state.is_terminal() and move_count < max_moves:
        # Roll dice
        dice1 = random.randint(1, 6)
        dice2 = random.randint(1, 6)
        
        # Choose action
        action = random_agent_move(state, dice1, dice2)
        
        # Execute move
        state, move_info = engine.execute_move(state, dice1, dice2, action)
        replay.add_move(move_info)
        move_count += 1
        
        # Print move
        print(f"\nMove {move_count}: {move_info}")
        
        # Show state every 10 moves or at end
        if move_count % 10 == 0 or state.is_terminal():
            print()
            state.pretty_print()
    
    # Print summary
    print("\n" + "="*70)
    replay.print_summary()
    
    # Print statistics
    stats = replay.get_statistics()
    print("\nGame Statistics:")
    print(f"  Ladders hit: {stats['ladders_hit']}")
    print(f"  Snakes hit: {stats['snakes_hit']}")
    print(f"  Scorpions hit: {stats['scorpions_hit']}")
    print(f"  Grapes collected: {stats['grapes_hit']}")
    print(f"  Captures by Player A: {stats['captures_by_a']}")
    print(f"  Captures by Player B: {stats['captures_by_b']}")
    print(f"  Illegal moves: {stats['illegal_moves']}")
    print()


if __name__ == '__main__':
    random.seed(42)  # For reproducibility
    demo_simple_game()

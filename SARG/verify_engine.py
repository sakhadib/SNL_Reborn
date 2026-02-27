#!/usr/bin/env python3
"""
Quick verification that the game engine is working correctly.
Run this to verify the installation.
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

def verify_imports():
    """Verify all imports work."""
    print("Testing imports...")
    try:
        from src.engine import (
            Player, Action, SquareType,
            Board, CANONICAL_BOARD,
            GameState, GameEngine, GameReplay
        )
        from src.storage import GameStorage, GameWriter, GameReader
        print("✓ All imports successful")
        return True
    except Exception as e:
        print(f"✗ Import failed: {e}")
        return False


def verify_board():
    """Verify board configuration."""
    print("\nTesting board...")
    try:
        from src.engine import CANONICAL_BOARD
        
        assert len(CANONICAL_BOARD.SAFE_ZONES) == 5
        assert len(CANONICAL_BOARD.LADDERS) == 7
        assert len(CANONICAL_BOARD.SNAKES) == 8
        assert len(CANONICAL_BOARD.SCORPIONS) == 6
        assert len(CANONICAL_BOARD.GRAPES) == 4
        
        print("✓ Board configuration valid")
        return True
    except Exception as e:
        print(f"✗ Board verification failed: {e}")
        return False


def verify_engine():
    """Verify game engine works."""
    print("\nTesting game engine...")
    try:
        from src.engine import GameEngine, GameState, Action
        
        engine = GameEngine()
        state = GameState.initial_state()
        
        # Execute a simple move
        new_state, move_info = engine.execute_move(state, 3, 5, Action.CHOOSE_DIE_1)
        
        assert new_state.a_position == 3
        assert move_info.chosen_die == 3
        assert new_state.current_player.value == 1  # Player B
        
        print("✓ Game engine working")
        return True
    except Exception as e:
        print(f"✗ Engine verification failed: {e}")
        return False


def verify_storage():
    """Verify binary storage."""
    print("\nTesting binary storage...")
    try:
        from src.storage import Move
        
        # Test move encoding/decoding
        move = Move(dice1=6, dice2=3, action=1)
        data = move.to_bytes()
        decoded = Move.from_bytes(data)
        
        assert decoded.dice1 == 6
        assert decoded.dice2 == 3
        assert decoded.action == 1
        
        print("✓ Binary storage working")
        return True
    except Exception as e:
        print(f"✗ Storage verification failed: {e}")
        return False


def main():
    """Run all verifications."""
    print("="*60)
    print("SARG Game Engine Verification")
    print("="*60)
    
    results = []
    results.append(("Imports", verify_imports()))
    results.append(("Board", verify_board()))
    results.append(("Engine", verify_engine()))
    results.append(("Storage", verify_storage()))
    
    print("\n" + "="*60)
    print("VERIFICATION RESULTS")
    print("="*60)
    
    for name, passed in results:
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"{name:20s} {status}")
    
    all_passed = all(result for _, result in results)
    
    print("="*60)
    if all_passed:
        print("✓ ALL CHECKS PASSED - Engine ready to use!")
        return 0
    else:
        print("✗ SOME CHECKS FAILED - Please review errors above")
        return 1


if __name__ == '__main__':
    sys.exit(main())

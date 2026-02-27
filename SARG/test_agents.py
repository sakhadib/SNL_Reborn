#!/usr/bin/env python3
"""
Quick test to verify all 15 agents can play games successfully.
"""

from src.agents import AGENT_REGISTRY
from src.engine import GameEngine, GameState, Player
import random

def test_all_agents():
    """Test that all agents can play a game."""
    print("Testing all 15 heuristic agents...")
    print("=" * 60)
    
    agent_names = list(AGENT_REGISTRY.keys())
    
    # Test each agent against MAXIM
    for agent_name in agent_names:
        print(f"\nTesting {agent_name.upper()}...", end=" ")
        
        try:
            # Create agents
            agent = AGENT_REGISTRY[agent_name]()
            opponent = AGENT_REGISTRY['maxim']()
            
            # Play a quick game
            random.seed(42)
            engine = GameEngine()
            state = GameState.initial_state(engine.board)
            
            turn = 0
            max_turns = 500  # Safety limit
            
            while not state.is_terminal() and turn < max_turns:
                turn += 1
                current_player = state.current_player
                
                # Roll dice
                dice1 = random.randint(1, 6)
                dice2 = random.randint(1, 6)
                
                # Get action
                current_agent = agent if current_player == Player.A else opponent
                action = current_agent.choose_action(engine, state, current_player, dice1, dice2)
                
                # Execute move
                state, move_info = engine.execute_move(state, dice1, dice2, action)
            
            if state.is_terminal():
                winner = state.get_winner()
                winner_name = "Agent" if winner == Player.A else "MAXIM"
                print(f"✅ OK - Game ended in {turn} turns, winner: {winner_name}")
            else:
                print(f"⚠️  Timeout after {max_turns} turns")
                
        except Exception as e:
            print(f"❌ FAILED - {e}")
            return False
    
    print("\n" + "=" * 60)
    print("✅ All agents tested successfully!")
    return True


if __name__ == "__main__":
    success = test_all_agents()
    exit(0 if success else 1)

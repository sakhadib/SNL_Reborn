"""
Agents Package - Heuristic and learning agents for SARG.
"""

from .base_agent import BaseAgent, AgentHelper
from .heuristic_agents import (
    MaximAgent,
    MinimAgent,
    ExactorAgent,
    SnakeAvoiderAgent,
    ScorpionAvoiderAgent,
    SafePreferrerAgent,
    HunterAgent,
    SafeHunterAgent,
    AntiCaptureAgent,
    GrapeSeekerAgent,
    ImmuneAggressorAgent,
    StunExploiterAgent,
    BalancedEvalAgent,
    RiskSeekerAgent,
    RiskAverseAgent,
)

# Registry of all agents by name
AGENT_REGISTRY = {
    'maxim': MaximAgent,
    'minim': MinimAgent,
    'exactor': ExactorAgent,
    'snake_avoider': SnakeAvoiderAgent,
    'scorpion_avoider': ScorpionAvoiderAgent,
    'safe_preferrer': SafePreferrerAgent,
    'hunter': HunterAgent,
    'safe_hunter': SafeHunterAgent,
    'anti_capture': AntiCaptureAgent,
    'grape_seeker': GrapeSeekerAgent,
    'immune_aggressor': ImmuneAggressorAgent,
    'stun_exploiter': StunExploiterAgent,
    'opportunistic': StunExploiterAgent,
    'balanced_eval': BalancedEvalAgent,
    'risk_seeker': RiskSeekerAgent,
    'risk_averse': RiskAverseAgent,
}

__all__ = [
    'BaseAgent',
    'AgentHelper',
    'MaximAgent',
    'MinimAgent',
    'ExactorAgent',
    'SnakeAvoiderAgent',
    'ScorpionAvoiderAgent',
    'SafePreferrerAgent',
    'HunterAgent',
    'SafeHunterAgent',
    'AntiCaptureAgent',
    'GrapeSeekerAgent',
    'ImmuneAggressorAgent',
    'StunExploiterAgent',
    'BalancedEvalAgent',
    'RiskSeekerAgent',
    'RiskAverseAgent',
    'AGENT_REGISTRY',
]

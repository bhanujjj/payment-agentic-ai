"""
Action learner.

Learns from past outcomes to improve future decisions.
"""

import logging
from typing import Optional, Dict

from agent.memory import ActionMemory
from agent.learning_models import OutcomeClassification


class ActionLearner:
    """
    Learns from action outcomes and adjusts decision weights.
    
    Uses deterministic rules based on past success/failure rates.
    """
    
    def __init__(self, memory: ActionMemory):
        """
        Initialize learner.
        
        Args:
            memory: ActionMemory instance
        """
        self.memory = memory
        self.logger = logging.getLogger(__name__)
        
        # Learning parameters (bounded)
        self.max_boost = 0.2      # Max 20% boost
        self.max_penalty = 0.2    # Max 20% penalty
        self.min_samples = 2      # Need at least 2 samples to learn
    
    def get_learned_weight_adjustment(
        self,
        action: str,
        context_summary: str
    ) -> float:
        """
        Get weight adjustment based on past outcomes.
        
        Args:
            action: Action being considered
            context_summary: Current context description
            
        Returns:
            Adjustment factor (0.8 to 1.2)
            - 1.0 = no adjustment
            - >1.0 = boost (action worked before)
            - <1.0 = penalty (action failed before)
        """
        # Get similar past outcomes
        similar = self.memory.get_similar(context_summary, action, max_results=10)
        
        if len(similar) < self.min_samples:
            # Not enough data to learn
            return 1.0
        
        # Count outcomes
        successes = sum(1 for o in similar if o.outcome == OutcomeClassification.SUCCESS)
        neutrals = sum(1 for o in similar if o.outcome == OutcomeClassification.NEUTRAL)
        failures = sum(1 for o in similar if o.outcome == OutcomeClassification.FAILURE)
        
        total = len(similar)
        success_rate = successes / total
        failure_rate = failures / total
        
        # Calculate adjustment
        if success_rate > 0.6:
            # Action worked well before - boost it
            boost = min(self.max_boost, (success_rate - 0.5) * 0.4)
            adjustment = 1.0 + boost
            
            self.logger.info(
                f"✓ Past {action} succeeded {successes}/{total} times in similar context "
                f"→ boosting score by {boost:.0%}"
            )
        elif failure_rate > 0.6:
            # Action failed before - penalize it
            penalty = min(self.max_penalty, (failure_rate - 0.5) * 0.4)
            adjustment = 1.0 - penalty
            
            self.logger.info(
                f"✗ Past {action} failed {failures}/{total} times in similar context "
                f"→ reducing score by {penalty:.0%}"
            )
        else:
            # Mixed results - no strong signal
            adjustment = 1.0
            self.logger.debug(
                f"Mixed results for {action}: {successes}S/{neutrals}N/{failures}F "
                f"→ no adjustment"
            )
        
        return adjustment
    
    def get_action_confidence_boost(self, action: str) -> float:
        """
        Get confidence boost based on overall action success rate.
        
        Args:
            action: Action name
            
        Returns:
            Confidence boost (0.0 to 0.1)
        """
        stats = self.memory.get_action_stats(action)
        
        if not stats or stats.total_observations < self.min_samples:
            return 0.0
        
        # Boost confidence if action has high success rate
        if stats.success_rate > 0.7:
            boost = min(0.1, (stats.success_rate - 0.5) * 0.2)
            return boost
        
        return 0.0
    
    def get_learning_summary(self) -> Dict[str, any]:
        """Get summary of what has been learned."""
        summary = self.memory.get_summary()
        
        if summary['total'] == 0:
            return {'status': 'no_learning_data'}
        
        # Add action-specific insights
        insights = {}
        for action in summary.get('by_action', {}).keys():
            stats = self.memory.get_action_stats(action)
            if stats:
                insights[action] = {
                    'total': stats.total_observations,
                    'success_rate': f"{stats.success_rate:.0%}",
                    'avg_score': f"{stats.avg_outcome_score:.2f}",
                    'recommendation': self._get_recommendation(stats)
                }
        
        return {
            'status': 'learning_active',
            'total_observations': summary['total'],
            'insights': insights
        }
    
    def _get_recommendation(self, stats) -> str:
        """Get recommendation based on stats."""
        if stats.success_rate > 0.7:
            return "RECOMMENDED (high success rate)"
        elif stats.success_rate < 0.3:
            return "AVOID (high failure rate)"
        else:
            return "NEUTRAL (mixed results)"

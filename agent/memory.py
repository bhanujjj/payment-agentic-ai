"""
Action memory storage.

Stores and retrieves action outcomes for learning.
"""

import json
import logging
from pathlib import Path
from typing import List, Optional, Dict, Any
from datetime import datetime

from agent.learning_models import ActionOutcome, LearningStats, OutcomeClassification


class ActionMemory:
    """
    Stores action outcomes and provides retrieval for learning.
    
    Uses simple JSON file storage.
    """
    
    def __init__(self, storage_path: str = "./data/memory/action_memory.json"):
        """
        Initialize memory.
        
        Args:
            storage_path: Path to JSON storage file
        """
        self.storage_path = Path(storage_path)
        self.memories: List[ActionOutcome] = []
        self.logger = logging.getLogger(__name__)
        
        # Create directory if needed
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Load existing memories
        self.load()
    
    def add(self, outcome: ActionOutcome):
        """
        Store an action outcome.
        
        Args:
            outcome: ActionOutcome to store
        """
        self.memories.append(outcome)
        self.logger.info(
            f"Stored outcome: {outcome.action} → {outcome.outcome.value} "
            f"(score: {outcome.outcome_score:.2f})"
        )
        
        # Auto-save
        self.save()
    
    def get_all(self) -> List[ActionOutcome]:
        """Get all stored outcomes."""
        return self.memories.copy()
    
    def get_by_action(self, action: str) -> List[ActionOutcome]:
        """
        Get all outcomes for a specific action.
        
        Args:
            action: Action name
            
        Returns:
            List of outcomes for that action
        """
        return [m for m in self.memories if m.action == action]
    
    def get_similar(
        self,
        context_summary: str,
        action: str,
        max_results: int = 5
    ) -> List[ActionOutcome]:
        """
        Get similar past outcomes.
        
        Simple similarity: same action + keyword overlap in context.
        
        Args:
            context_summary: Current context description
            action: Action being considered
            max_results: Max number of results
            
        Returns:
            List of similar outcomes (most recent first)
        """
        # Get outcomes for this action
        action_outcomes = self.get_by_action(action)
        
        if not action_outcomes:
            return []
        
        # Simple keyword-based similarity
        context_keywords = set(context_summary.lower().split())
        
        # Score by keyword overlap
        scored = []
        for outcome in action_outcomes:
            outcome_keywords = set(outcome.context_summary.lower().split())
            overlap = len(context_keywords & outcome_keywords)
            scored.append((overlap, outcome))
        
        # Sort by overlap (descending), then by recency
        scored.sort(key=lambda x: (x[0], x[1].timestamp), reverse=True)
        
        # Return top results
        return [outcome for _, outcome in scored[:max_results]]
    
    def get_action_stats(self, action: str) -> Optional[LearningStats]:
        """
        Get statistics for an action.
        
        Args:
            action: Action name
            
        Returns:
            LearningStats or None if no data
        """
        outcomes = self.get_by_action(action)
        
        if not outcomes:
            return None
        
        success_count = sum(1 for o in outcomes if o.outcome == OutcomeClassification.SUCCESS)
        neutral_count = sum(1 for o in outcomes if o.outcome == OutcomeClassification.NEUTRAL)
        failure_count = sum(1 for o in outcomes if o.outcome == OutcomeClassification.FAILURE)
        
        avg_score = sum(o.outcome_score for o in outcomes) / len(outcomes)
        success_rate = success_count / len(outcomes) if outcomes else 0.0
        
        return LearningStats(
            action=action,
            total_observations=len(outcomes),
            success_count=success_count,
            neutral_count=neutral_count,
            failure_count=failure_count,
            avg_outcome_score=avg_score,
            success_rate=success_rate
        )
    
    def save(self):
        """Persist memories to JSON file."""
        try:
            data = {
                'version': '1.0',
                'saved_at': datetime.utcnow().isoformat(),
                'memories': [m.to_dict() for m in self.memories]
            }
            
            with open(self.storage_path, 'w') as f:
                json.dump(data, f, indent=2)
            
            self.logger.debug(f"Saved {len(self.memories)} memories to {self.storage_path}")
        except Exception as e:
            self.logger.error(f"Failed to save memories: {e}")
    
    def load(self):
        """Load memories from JSON file."""
        if not self.storage_path.exists():
            self.logger.info("No existing memory file found. Starting fresh.")
            return
        
        try:
            with open(self.storage_path, 'r') as f:
                data = json.load(f)
            
            self.memories = [
                ActionOutcome.from_dict(m) for m in data.get('memories', [])
            ]
            
            self.logger.info(f"Loaded {len(self.memories)} memories from {self.storage_path}")
        except Exception as e:
            self.logger.error(f"Failed to load memories: {e}")
            self.memories = []
    
    def clear(self):
        """Clear all memories."""
        self.memories = []
        self.save()
        self.logger.info("Cleared all memories")
    
    def get_summary(self) -> Dict[str, Any]:
        """Get summary statistics."""
        if not self.memories:
            return {'total': 0}
        
        by_action = {}
        for memory in self.memories:
            if memory.action not in by_action:
                by_action[memory.action] = []
            by_action[memory.action].append(memory)
        
        return {
            'total': len(self.memories),
            'by_action': {
                action: {
                    'count': len(outcomes),
                    'success': sum(1 for o in outcomes if o.outcome == OutcomeClassification.SUCCESS),
                    'neutral': sum(1 for o in outcomes if o.outcome == OutcomeClassification.NEUTRAL),
                    'failure': sum(1 for o in outcomes if o.outcome == OutcomeClassification.FAILURE),
                }
                for action, outcomes in by_action.items()
            }
        }

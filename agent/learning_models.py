"""
Learning data models.

Defines structures for storing action outcomes and learning from them.
"""

from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import Dict, Any, Optional
from enum import Enum


class OutcomeClassification(Enum):
    """Classification of action outcome."""
    SUCCESS = "SUCCESS"
    NEUTRAL = "NEUTRAL"
    FAILURE = "FAILURE"


@dataclass
class ActionOutcome:
    """
    Record of an action and its measured outcome.
    
    This is what the agent learns from.
    """
    # Context
    context_summary: str          # "retry storm, 85% success, HDFC degraded"
    action: str                   # "recommend_retry_adjustment"
    risk_level: str               # "LOW", "MEDIUM", "HIGH"
    
    # Pre-action metrics (baseline)
    pre_success_rate: float
    pre_latency_ms: float
    pre_retry_count: int
    pre_error_rate: float
    
    # Post-action metrics (after action applied)
    post_success_rate: float
    post_latency_ms: float
    post_retry_count: int
    post_error_rate: float
    
    # Computed impact (delta)
    success_rate_delta: float     # +0.08 = improved
    latency_delta: float          # -130 = improved
    retry_delta: int              # -40 = improved
    error_rate_delta: float       # -0.05 = improved
    
    # Evaluation
    outcome: OutcomeClassification
    outcome_score: float          # 0.0 (worst) to 1.0 (best)
    
    # Metadata
    timestamp: datetime
    notes: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage."""
        data = asdict(self)
        data['outcome'] = self.outcome.value
        data['timestamp'] = self.timestamp.isoformat()
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ActionOutcome':
        """Create from dictionary."""
        data = data.copy()
        data['outcome'] = OutcomeClassification(data['outcome'])
        data['timestamp'] = datetime.fromisoformat(data['timestamp'])
        return cls(**data)


@dataclass
class LearningStats:
    """
    Statistics about learned patterns.
    """
    action: str
    total_observations: int
    success_count: int
    neutral_count: int
    failure_count: int
    avg_outcome_score: float
    success_rate: float
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)

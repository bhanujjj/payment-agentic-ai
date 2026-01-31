"""
Decision models - Structured representations of decisions and actions.

These models define the shape of decision outputs from the decision engine.
"""

from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional
from enum import Enum


class ActionType(Enum):
    """Available action types."""
    DO_NOTHING = "do_nothing"
    ALERT_OPS = "alert_ops"
    RECOMMEND_REROUTE = "recommend_reroute"
    RECOMMEND_RETRY_REDUCTION = "recommend_retry_reduction"
    RECOMMEND_PATH_SUPPRESSION = "recommend_path_suppression"
    RECOMMEND_CIRCUIT_BREAKER = "recommend_circuit_breaker"
    RECOMMEND_RATE_LIMIT = "recommend_rate_limit"


class RiskLevel(Enum):
    """Risk levels for actions."""
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


@dataclass
class ActionScore:
    """
    Score for a single action.
    
    Represents the evaluation of one possible action.
    """
    action: str
    score: float  # 0-1
    
    # Impact metrics
    expected_success_rate_impact: float = 0.0  # -1 to 1
    expected_latency_impact: float = 0.0  # -1 to 1
    expected_cost_impact: float = 0.0  # -1 to 1
    
    # Risk and constraints
    risk_level: RiskLevel = RiskLevel.LOW
    reversibility: float = 1.0  # 0-1, how easy to undo
    
    # Reasoning
    reasoning: str = ""
    
    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        data = asdict(self)
        data['risk_level'] = self.risk_level.value
        return data


@dataclass
class Decision:
    """
    Final decision output from the decision engine.
    
    This is what the agent decides to do based on reasoning.
    """
    # Selected action
    selected_action: str
    confidence: float  # 0-1
    
    # Risk and approval
    risk_level: RiskLevel
    requires_human_approval: bool
    
    # Reasoning
    reasoning_summary: str
    
    # All considered actions with scores
    considered_actions: List[ActionScore] = field(default_factory=list)
    
    # Constraints that influenced decision
    active_constraints: List[str] = field(default_factory=list)
    
    # Rejected actions and why
    rejected_actions: Dict[str, str] = field(default_factory=dict)
    
    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return {
            "selected_action": self.selected_action,
            "confidence": self.confidence,
            "risk_level": self.risk_level.value,
            "requires_human_approval": self.requires_human_approval,
            "reasoning_summary": self.reasoning_summary,
            "considered_actions": [
                {
                    "action": action.action,
                    "score": action.score
                }
                for action in sorted(self.considered_actions, key=lambda x: x.score, reverse=True)
            ],
            "active_constraints": self.active_constraints,
            "rejected_actions": self.rejected_actions
        }
    
    def get_summary(self) -> str:
        """Get human-readable summary."""
        lines = [
            f"Decision: {self.selected_action}",
            f"  Confidence: {self.confidence:.0%}",
            f"  Risk Level: {self.risk_level.value}",
            f"  Requires Approval: {'Yes' if self.requires_human_approval else 'No'}",
            f"  Reasoning: {self.reasoning_summary}"
        ]
        
        if self.considered_actions:
            lines.append("\n  Considered Actions:")
            for action in sorted(self.considered_actions, key=lambda x: x.score, reverse=True)[:3]:
                lines.append(f"    • {action.action}: {action.score:.0%}")
        
        return "\n".join(lines)


@dataclass
class DecisionConstraints:
    """
    Constraints that govern decision making.
    
    These are the guardrails and limits.
    """
    # Risk thresholds
    max_auto_approve_risk: RiskLevel = RiskLevel.LOW
    min_confidence_for_action: float = 0.5
    
    # Impact limits (max allowed negative impact)
    max_allowed_success_rate_drop: float = 0.05  # 5%
    max_allowed_latency_increase: float = 0.2  # 20%
    max_allowed_cost_increase: float = 0.3  # 30%
    
    # Reversibility requirement
    min_reversibility_for_high_risk: float = 0.7
    
    # Specific action constraints
    allow_rerouting: bool = True
    allow_path_suppression: bool = True
    allow_circuit_breaker: bool = True
    
    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        data = asdict(self)
        data['max_auto_approve_risk'] = self.max_auto_approve_risk.value
        return data

"""
Execution data models.

Defines structures for action execution results and system state.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, Any, List, Optional
from enum import Enum


class ExecutionStatus(Enum):
    """Status of action execution."""
    EXECUTED = "EXECUTED"
    PENDING_HUMAN_APPROVAL = "PENDING_HUMAN_APPROVAL"
    BLOCKED = "BLOCKED"
    FAILED = "FAILED"


@dataclass
class ExecutionResult:
    """
    Result of executing an action.
    
    This is returned by the executor to indicate what happened
    when attempting to execute a decision.
    """
    action: str
    executed: bool
    status: ExecutionStatus
    impact_scope: str
    expected_effect: str
    timestamp: datetime
    state_changes: Dict[str, Any] = field(default_factory=dict)
    reasoning: str = ""
    error: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for logging/serialization."""
        return {
            "action": self.action,
            "executed": self.executed,
            "status": self.status.value,
            "impact_scope": self.impact_scope,
            "expected_effect": self.expected_effect,
            "timestamp": self.timestamp.isoformat(),
            "state_changes": self.state_changes,
            "reasoning": self.reasoning,
            "error": self.error
        }


@dataclass
class SystemState:
    """
    Current state of the payment system.
    
    This represents the configuration that the executor can modify.
    All changes are simulated - no real system impact.
    """
    # Routing configuration
    routing_overrides: Dict[str, str] = field(default_factory=dict)  # bank -> "suppressed" | "rerouted"
    
    # Retry configuration
    retry_policy: Dict[str, Any] = field(default_factory=lambda: {
        "max_retries": 3,
        "backoff_ms": 1000
    })
    
    # Circuit breakers
    circuit_breakers: Dict[str, bool] = field(default_factory=dict)  # bank -> enabled
    
    # Rate limits
    rate_limits: Dict[str, int] = field(default_factory=dict)  # bank -> requests/sec
    
    # Active alerts
    alerts: List[str] = field(default_factory=list)
    
    # Metadata
    last_updated: datetime = field(default_factory=datetime.utcnow)
    last_action: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "routing_overrides": self.routing_overrides,
            "retry_policy": self.retry_policy,
            "circuit_breakers": self.circuit_breakers,
            "rate_limits": self.rate_limits,
            "alerts": self.alerts,
            "last_updated": self.last_updated.isoformat(),
            "last_action": self.last_action
        }
    
    def reset(self):
        """Reset to default state."""
        self.routing_overrides.clear()
        self.retry_policy = {"max_retries": 3, "backoff_ms": 1000}
        self.circuit_breakers.clear()
        self.rate_limits.clear()
        self.alerts.clear()
        self.last_updated = datetime.utcnow()
        self.last_action = None

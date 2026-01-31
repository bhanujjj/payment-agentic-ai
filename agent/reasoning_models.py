"""
Reasoning models - Structured outputs from the reasoning layer.

These models define the shape of reasoning results.
"""

from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional


@dataclass
class ReasoningResult:
    """
    Structured output from the reasoning layer.
    
    This represents the agent's interpretation and hypotheses
    about the current payment system state.
    """
    # Hypotheses with confidence scores (0-1)
    hypotheses: Dict[str, float] = field(default_factory=dict)
    
    # Human-readable explanation
    explanation: str = ""
    
    # What the agent is assuming
    assumptions: List[str] = field(default_factory=list)
    
    # What the agent is uncertain about
    uncertainty: List[str] = field(default_factory=list)
    
    # Overall confidence in the reasoning (0-1)
    overall_confidence: float = 0.0
    
    # Raw LLM response (for debugging)
    raw_response: Optional[str] = None
    
    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return asdict(self)
    
    def get_top_hypothesis(self) -> Optional[tuple[str, float]]:
        """
        Get the hypothesis with highest confidence.
        
        Returns:
            Tuple of (hypothesis_name, confidence) or None
        """
        if not self.hypotheses:
            return None
        
        top = max(self.hypotheses.items(), key=lambda x: x[1])
        return top
    
    def get_summary(self) -> str:
        """Get human-readable summary."""
        lines = ["Reasoning Summary:"]
        
        if self.hypotheses:
            lines.append("\nTop Hypotheses:")
            sorted_hyp = sorted(
                self.hypotheses.items(),
                key=lambda x: x[1],
                reverse=True
            )
            for hyp, conf in sorted_hyp[:3]:
                lines.append(f"  • {hyp}: {conf:.0%} confidence")
        
        lines.append(f"\nOverall Confidence: {self.overall_confidence:.0%}")
        
        if self.explanation:
            lines.append(f"\nExplanation: {self.explanation}")
        
        return "\n".join(lines)


@dataclass
class HypothesisType:
    """Common hypothesis types for payment issues."""
    BANK_DEGRADATION = "bank_degradation"
    BANK_OUTAGE = "bank_outage"
    NETWORK_ISSUES = "network_issues"
    RETRY_STORM = "retry_storm"
    FRAUD_SPIKE = "fraud_spike"
    RATE_LIMITING = "rate_limiting"
    PAYMENT_METHOD_ISSUE = "payment_method_issue"
    NORMAL_OPERATION = "normal_operation"
    PEAK_LOAD = "peak_load"
    CONFIGURATION_ERROR = "configuration_error"

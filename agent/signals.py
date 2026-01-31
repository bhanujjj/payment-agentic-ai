"""
Signal models - Structured representations of computed signals.

Signals are high-level metrics derived from raw payment data
that the agent can reason over.
"""

from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional
from enum import Enum


class Trend(Enum):
    """Trend direction for metrics."""
    RISING = "rising"
    STABLE = "stable"
    FALLING = "falling"
    UNKNOWN = "unknown"


class Severity(Enum):
    """Severity level for issues."""
    NORMAL = "normal"
    WARNING = "warning"
    CRITICAL = "critical"


@dataclass
class PaymentSignals:
    """
    Aggregated signals from payment data over a time window.
    
    This is what the agent observes and reasons about.
    """
    # Time window
    window_start: str
    window_end: str
    window_duration_seconds: int
    
    # Volume metrics
    total_payments: int
    successful_payments: int
    failed_payments: int
    
    # Success/failure rates
    overall_success_rate: float
    overall_failure_rate: float
    
    # Bank-specific metrics
    bank_failure_rates: Dict[str, float] = field(default_factory=dict)
    bank_avg_latencies: Dict[str, float] = field(default_factory=dict)
    bank_volumes: Dict[str, int] = field(default_factory=dict)
    
    # Payment method metrics
    method_failure_rates: Dict[str, float] = field(default_factory=dict)
    method_avg_latencies: Dict[str, float] = field(default_factory=dict)
    method_volumes: Dict[str, int] = field(default_factory=dict)
    
    # Latency metrics
    avg_latency_ms: float = 0.0
    p50_latency_ms: float = 0.0
    p95_latency_ms: float = 0.0
    p99_latency_ms: float = 0.0
    
    # Trends
    latency_trend: Trend = Trend.UNKNOWN
    volume_trend: Trend = Trend.UNKNOWN
    failure_rate_trend: Trend = Trend.UNKNOWN
    
    # Retry metrics
    total_retries: int = 0
    retry_success_rate: float = 0.0
    retry_effectiveness: float = 0.0  # Positive = helpful, negative = harmful
    
    # Error distribution
    error_code_counts: Dict[str, int] = field(default_factory=dict)
    top_errors: List[str] = field(default_factory=list)
    
    # Anomaly indicators
    has_anomaly: bool = False
    anomaly_severity: Severity = Severity.NORMAL
    anomaly_description: str = ""
    
    # Problematic entities
    degraded_banks: List[str] = field(default_factory=list)
    degraded_methods: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict:
        """Convert signals to dictionary."""
        data = asdict(self)
        # Convert enums to values
        data['latency_trend'] = self.latency_trend.value
        data['volume_trend'] = self.volume_trend.value
        data['failure_rate_trend'] = self.failure_rate_trend.value
        data['anomaly_severity'] = self.anomaly_severity.value
        return data
    
    def get_summary(self) -> str:
        """Get human-readable summary of signals."""
        lines = [
            f"Payment Signals ({self.window_duration_seconds}s window)",
            f"  Total: {self.total_payments} payments",
            f"  Success Rate: {self.overall_success_rate:.1%}",
            f"  Avg Latency: {self.avg_latency_ms:.0f}ms",
        ]
        
        if self.degraded_banks:
            lines.append(f"  ⚠️  Degraded Banks: {', '.join(self.degraded_banks)}")
        
        if self.has_anomaly:
            lines.append(f"  🚨 Anomaly: {self.anomaly_description}")
        
        return "\n".join(lines)


@dataclass
class BankSignal:
    """Signals for a specific bank."""
    bank_name: str
    total_payments: int
    success_rate: float
    failure_rate: float
    avg_latency_ms: float
    is_degraded: bool = False
    severity: Severity = Severity.NORMAL

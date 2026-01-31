"""
Payment data models.

Defines the structure of payment records and related data types.
"""

from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import Optional, Dict, Any
from enum import Enum


class PaymentStatus(Enum):
    """Payment status types."""
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"
    PENDING = "PENDING"
    TIMEOUT = "TIMEOUT"


class PaymentMethod(Enum):
    """Payment method types."""
    UPI = "UPI"
    CREDIT_CARD = "CREDIT_CARD"
    DEBIT_CARD = "DEBIT_CARD"
    NET_BANKING = "NET_BANKING"
    WALLET = "WALLET"


class ErrorCode(Enum):
    """Payment error codes."""
    NONE = "NONE"
    INSUFFICIENT_FUNDS = "INSUFFICIENT_FUNDS"
    BANK_TIMEOUT = "BANK_TIMEOUT"
    INVALID_CREDENTIALS = "INVALID_CREDENTIALS"
    NETWORK_ERROR = "NETWORK_ERROR"
    RATE_LIMIT_EXCEEDED = "RATE_LIMIT_EXCEEDED"
    GATEWAY_ERROR = "GATEWAY_ERROR"
    FRAUD_SUSPECTED = "FRAUD_SUSPECTED"
    TECHNICAL_ERROR = "TECHNICAL_ERROR"


@dataclass
class PaymentRecord:
    """
    Represents a single payment transaction.
    
    This is the core data structure that the agent will observe and act upon.
    """
    payment_id: str
    timestamp: datetime
    payment_method: PaymentMethod
    bank: str
    amount: float
    currency: str
    status: PaymentStatus
    error_code: ErrorCode
    latency_ms: int
    retry_count: int = 0
    merchant_id: Optional[str] = None
    customer_id: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert payment record to dictionary.
        
        Returns:
            Dictionary representation with serialized enums and datetime
        """
        data = asdict(self)
        data['timestamp'] = self.timestamp.isoformat()
        data['payment_method'] = self.payment_method.value
        data['status'] = self.status.value
        data['error_code'] = self.error_code.value
        return data
    
    def is_failed(self) -> bool:
        """Check if payment failed."""
        return self.status in [PaymentStatus.FAILED, PaymentStatus.TIMEOUT]
    
    def is_successful(self) -> bool:
        """Check if payment succeeded."""
        return self.status == PaymentStatus.SUCCESS
    
    def should_retry(self) -> bool:
        """
        Determine if payment should be retried based on error type.
        
        Returns:
            True if error is retryable
        """
        retryable_errors = {
            ErrorCode.BANK_TIMEOUT,
            ErrorCode.NETWORK_ERROR,
            ErrorCode.GATEWAY_ERROR,
            ErrorCode.TECHNICAL_ERROR
        }
        return self.error_code in retryable_errors and self.retry_count < 3


@dataclass
class BankHealth:
    """
    Represents the health status of a bank/payment provider.
    
    Used to simulate degraded performance or outages.
    """
    bank_name: str
    success_rate: float = 0.95  # 95% success rate by default
    avg_latency_ms: int = 200
    is_degraded: bool = False
    is_down: bool = False
    error_rate_multiplier: float = 1.0
    
    def get_effective_success_rate(self) -> float:
        """Get current success rate accounting for degradation."""
        if self.is_down:
            return 0.0
        if self.is_degraded:
            return self.success_rate * 0.5  # 50% of normal during degradation
        return self.success_rate
    
    def get_effective_latency(self) -> int:
        """Get current latency accounting for degradation."""
        if self.is_down:
            return 30000  # 30 second timeout
        if self.is_degraded:
            return int(self.avg_latency_ms * 3)  # 3x slower
        return self.avg_latency_ms

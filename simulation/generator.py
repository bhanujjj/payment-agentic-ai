"""
Payment data generator.

Generates realistic payment transaction data with configurable failure scenarios.
"""

import random
import uuid
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import logging

from simulation.models import (
    PaymentRecord,
    PaymentStatus,
    PaymentMethod,
    ErrorCode,
    BankHealth
)


class PaymentGenerator:
    """
    Generates realistic payment transaction data.
    
    Supports various failure scenarios:
    - Bank degradation
    - High latency periods
    - Retry storms
    - Specific error patterns
    """
    
    # Realistic bank names for Indian payment ecosystem
    BANKS = [
        "HDFC Bank",
        "ICICI Bank",
        "State Bank of India",
        "Axis Bank",
        "Kotak Mahindra Bank",
        "Yes Bank",
        "IDFC First Bank",
        "Paytm Payments Bank"
    ]
    
    # Typical payment amount distribution (in INR)
    AMOUNT_RANGES = [
        (50, 500, 0.4),      # Small transactions - 40%
        (500, 2000, 0.3),    # Medium transactions - 30%
        (2000, 10000, 0.2),  # Large transactions - 20%
        (10000, 50000, 0.1)  # Very large transactions - 10%
    ]
    
    def __init__(self, config: Optional[Dict] = None):
        """
        Initialize payment generator.
        
        Args:
            config: Configuration dictionary with:
                - base_failure_rate: Base probability of failure (default: 0.05)
                - base_latency_ms: Base latency in ms (default: 200)
                - enable_scenarios: Enable scenario simulation (default: True)
                - seed: Random seed for reproducibility
        """
        self.config = config or {}
        self.logger = logging.getLogger(__name__)
        
        # Configuration
        self.base_failure_rate = self.config.get('base_failure_rate', 0.05)
        self.base_latency_ms = self.config.get('base_latency_ms', 200)
        self.enable_scenarios = self.config.get('enable_scenarios', True)
        
        # Set random seed if provided
        seed = self.config.get('seed')
        if seed is not None:
            random.seed(seed)
        
        # Initialize bank health tracking
        self.bank_health: Dict[str, BankHealth] = {
            bank: BankHealth(
                bank_name=bank,
                success_rate=0.95 + random.uniform(-0.03, 0.03),  # 92-98%
                avg_latency_ms=random.randint(150, 300)
            )
            for bank in self.BANKS
        }
        
        # Scenario state
        self.current_time = datetime.utcnow()
        self.payment_counter = 0
        
    def generate_payment(
        self,
        payment_method: Optional[PaymentMethod] = None,
        bank: Optional[str] = None,
        force_failure: bool = False
    ) -> PaymentRecord:
        """
        Generate a single payment record.
        
        Args:
            payment_method: Specific payment method (random if None)
            bank: Specific bank (random if None)
            force_failure: Force this payment to fail
            
        Returns:
            Generated payment record
        """
        self.payment_counter += 1
        
        # Select payment method
        if payment_method is None:
            payment_method = random.choice(list(PaymentMethod))
        
        # Select bank
        if bank is None:
            bank = random.choice(self.BANKS)
        
        # Generate amount based on realistic distribution
        amount = self._generate_amount()
        
        # Get bank health
        bank_health = self.bank_health[bank]
        
        # Determine if payment succeeds
        success_rate = bank_health.get_effective_success_rate()
        if force_failure:
            will_succeed = False
        else:
            will_succeed = random.random() < success_rate
        
        # Generate latency
        latency_ms = self._generate_latency(bank_health, will_succeed)
        
        # Determine status and error
        if will_succeed:
            status = PaymentStatus.SUCCESS
            error_code = ErrorCode.NONE
        else:
            status, error_code = self._generate_failure(bank_health, latency_ms)
        
        # Create payment record
        payment = PaymentRecord(
            payment_id=f"PAY_{uuid.uuid4().hex[:12].upper()}",
            timestamp=self.current_time,
            payment_method=payment_method,
            bank=bank,
            amount=amount,
            currency="INR",
            status=status,
            error_code=error_code,
            latency_ms=latency_ms,
            retry_count=0,
            merchant_id=f"MERCH_{random.randint(1000, 9999)}",
            customer_id=f"CUST_{random.randint(10000, 99999)}",
            metadata={}
        )
        
        return payment
    
    def generate_batch(
        self,
        count: int,
        time_span_seconds: int = 60
    ) -> List[PaymentRecord]:
        """
        Generate a batch of payment records over a time span.
        
        Args:
            count: Number of payments to generate
            time_span_seconds: Time span to distribute payments over
            
        Returns:
            List of payment records
        """
        payments = []
        
        for i in range(count):
            # Distribute payments across time span
            offset_seconds = (i / count) * time_span_seconds
            self.current_time = datetime.utcnow() + timedelta(seconds=offset_seconds)
            
            payment = self.generate_payment()
            payments.append(payment)
        
        return payments
    
    def simulate_bank_degradation(
        self,
        bank: str,
        duration_seconds: int = 300
    ):
        """
        Simulate a bank experiencing degraded performance.
        
        Args:
            bank: Bank name to degrade
            duration_seconds: How long degradation lasts
        """
        if bank in self.bank_health:
            self.bank_health[bank].is_degraded = True
            self.logger.warning(f"Bank degradation started: {bank}")
    
    def simulate_bank_outage(
        self,
        bank: str,
        duration_seconds: int = 600
    ):
        """
        Simulate a complete bank outage.
        
        Args:
            bank: Bank name to take down
            duration_seconds: How long outage lasts
        """
        if bank in self.bank_health:
            self.bank_health[bank].is_down = True
            self.logger.error(f"Bank outage started: {bank}")
    
    def restore_bank(self, bank: str):
        """
        Restore a bank to normal operation.
        
        Args:
            bank: Bank name to restore
        """
        if bank in self.bank_health:
            self.bank_health[bank].is_degraded = False
            self.bank_health[bank].is_down = False
            self.logger.info(f"Bank restored: {bank}")
    
    def simulate_retry_storm(
        self,
        original_payment: PaymentRecord,
        retry_count: int = 3
    ) -> List[PaymentRecord]:
        """
        Simulate retry attempts for a failed payment.
        
        Args:
            original_payment: The original failed payment
            retry_count: Number of retries to generate
            
        Returns:
            List of retry payment records
        """
        retries = []
        
        for i in range(1, retry_count + 1):
            # Retries happen with exponential backoff
            retry_delay = 2 ** i  # 2, 4, 8 seconds
            retry_time = original_payment.timestamp + timedelta(seconds=retry_delay)
            
            # Create retry payment
            retry = PaymentRecord(
                payment_id=original_payment.payment_id,  # Same payment ID
                timestamp=retry_time,
                payment_method=original_payment.payment_method,
                bank=original_payment.bank,
                amount=original_payment.amount,
                currency=original_payment.currency,
                status=original_payment.status,  # May still fail
                error_code=original_payment.error_code,
                latency_ms=self._generate_latency(
                    self.bank_health[original_payment.bank],
                    False
                ),
                retry_count=i,
                merchant_id=original_payment.merchant_id,
                customer_id=original_payment.customer_id,
                metadata={"is_retry": True, "original_attempt": 0}
            )
            
            retries.append(retry)
        
        return retries
    
    def _generate_amount(self) -> float:
        """Generate realistic payment amount."""
        # Select range based on probability distribution
        rand = random.random()
        cumulative = 0.0
        
        for min_amt, max_amt, probability in self.AMOUNT_RANGES:
            cumulative += probability
            if rand <= cumulative:
                # Generate amount in this range
                amount = random.uniform(min_amt, max_amt)
                # Round to 2 decimal places
                return round(amount, 2)
        
        # Fallback
        return round(random.uniform(100, 1000), 2)
    
    def _generate_latency(
        self,
        bank_health: BankHealth,
        will_succeed: bool
    ) -> int:
        """
        Generate realistic latency.
        
        Args:
            bank_health: Bank health status
            will_succeed: Whether payment will succeed
            
        Returns:
            Latency in milliseconds
        """
        base_latency = bank_health.get_effective_latency()
        
        # Add some random variation (±30%)
        variation = random.uniform(0.7, 1.3)
        latency = int(base_latency * variation)
        
        # Failed payments often have higher latency (timeouts)
        if not will_succeed:
            if random.random() < 0.3:  # 30% of failures are timeouts
                latency = random.randint(5000, 30000)  # 5-30 seconds
        
        return latency
    
    def _generate_failure(
        self,
        bank_health: BankHealth,
        latency_ms: int
    ) -> tuple[PaymentStatus, ErrorCode]:
        """
        Generate failure status and error code.
        
        Args:
            bank_health: Bank health status
            latency_ms: Payment latency
            
        Returns:
            Tuple of (status, error_code)
        """
        # If latency is very high, it's likely a timeout
        if latency_ms > 10000:
            return PaymentStatus.TIMEOUT, ErrorCode.BANK_TIMEOUT
        
        # Otherwise, select error based on bank health
        if bank_health.is_down:
            return PaymentStatus.FAILED, ErrorCode.GATEWAY_ERROR
        
        if bank_health.is_degraded:
            # During degradation, more timeouts and technical errors
            error_weights = [
                (ErrorCode.BANK_TIMEOUT, 0.4),
                (ErrorCode.TECHNICAL_ERROR, 0.3),
                (ErrorCode.NETWORK_ERROR, 0.2),
                (ErrorCode.GATEWAY_ERROR, 0.1)
            ]
        else:
            # Normal failure distribution
            error_weights = [
                (ErrorCode.INSUFFICIENT_FUNDS, 0.3),
                (ErrorCode.INVALID_CREDENTIALS, 0.2),
                (ErrorCode.BANK_TIMEOUT, 0.15),
                (ErrorCode.NETWORK_ERROR, 0.15),
                (ErrorCode.TECHNICAL_ERROR, 0.1),
                (ErrorCode.RATE_LIMIT_EXCEEDED, 0.05),
                (ErrorCode.FRAUD_SUSPECTED, 0.03),
                (ErrorCode.GATEWAY_ERROR, 0.02)
            ]
        
        # Select error based on weights
        rand = random.random()
        cumulative = 0.0
        
        for error_code, weight in error_weights:
            cumulative += weight
            if rand <= cumulative:
                return PaymentStatus.FAILED, error_code
        
        # Fallback
        return PaymentStatus.FAILED, ErrorCode.TECHNICAL_ERROR
    
    def get_bank_health_summary(self) -> Dict[str, Dict]:
        """
        Get summary of all bank health statuses.
        
        Returns:
            Dictionary mapping bank names to health info
        """
        return {
            bank: {
                "success_rate": health.get_effective_success_rate(),
                "avg_latency_ms": health.get_effective_latency(),
                "is_degraded": health.is_degraded,
                "is_down": health.is_down
            }
            for bank, health in self.bank_health.items()
        }

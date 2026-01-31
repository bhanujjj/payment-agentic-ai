"""
Tests for payment data models.
"""

import pytest
from datetime import datetime

from simulation.models import (
    PaymentRecord,
    PaymentStatus,
    PaymentMethod,
    ErrorCode,
    BankHealth
)


class TestPaymentRecord:
    """Test cases for PaymentRecord."""
    
    def test_payment_record_creation(self):
        """Test creating a payment record."""
        payment = PaymentRecord(
            payment_id="PAY_TEST123",
            timestamp=datetime.utcnow(),
            payment_method=PaymentMethod.UPI,
            bank="HDFC Bank",
            amount=1000.50,
            currency="INR",
            status=PaymentStatus.SUCCESS,
            error_code=ErrorCode.NONE,
            latency_ms=200,
            retry_count=0
        )
        
        assert payment.payment_id == "PAY_TEST123"
        assert payment.amount == 1000.50
        assert payment.status == PaymentStatus.SUCCESS
    
    def test_payment_to_dict(self):
        """Test converting payment to dictionary."""
        payment = PaymentRecord(
            payment_id="PAY_TEST123",
            timestamp=datetime.utcnow(),
            payment_method=PaymentMethod.CREDIT_CARD,
            bank="ICICI Bank",
            amount=500.0,
            currency="INR",
            status=PaymentStatus.FAILED,
            error_code=ErrorCode.INSUFFICIENT_FUNDS,
            latency_ms=150,
            retry_count=1
        )
        
        payment_dict = payment.to_dict()
        
        assert payment_dict['payment_id'] == "PAY_TEST123"
        assert payment_dict['payment_method'] == "CREDIT_CARD"
        assert payment_dict['status'] == "FAILED"
        assert payment_dict['error_code'] == "INSUFFICIENT_FUNDS"
        assert isinstance(payment_dict['timestamp'], str)
    
    def test_is_failed(self):
        """Test is_failed method."""
        failed_payment = PaymentRecord(
            payment_id="PAY_FAIL",
            timestamp=datetime.utcnow(),
            payment_method=PaymentMethod.UPI,
            bank="Test Bank",
            amount=100.0,
            currency="INR",
            status=PaymentStatus.FAILED,
            error_code=ErrorCode.NETWORK_ERROR,
            latency_ms=5000,
            retry_count=0
        )
        
        assert failed_payment.is_failed() is True
        assert failed_payment.is_successful() is False
    
    def test_should_retry(self):
        """Test should_retry logic."""
        # Retryable error
        retryable = PaymentRecord(
            payment_id="PAY_RETRY",
            timestamp=datetime.utcnow(),
            payment_method=PaymentMethod.UPI,
            bank="Test Bank",
            amount=100.0,
            currency="INR",
            status=PaymentStatus.FAILED,
            error_code=ErrorCode.BANK_TIMEOUT,
            latency_ms=5000,
            retry_count=0
        )
        
        assert retryable.should_retry() is True
        
        # Non-retryable error
        non_retryable = PaymentRecord(
            payment_id="PAY_NO_RETRY",
            timestamp=datetime.utcnow(),
            payment_method=PaymentMethod.UPI,
            bank="Test Bank",
            amount=100.0,
            currency="INR",
            status=PaymentStatus.FAILED,
            error_code=ErrorCode.INSUFFICIENT_FUNDS,
            latency_ms=200,
            retry_count=0
        )
        
        assert non_retryable.should_retry() is False


class TestBankHealth:
    """Test cases for BankHealth."""
    
    def test_normal_bank_health(self):
        """Test normal bank health."""
        bank = BankHealth(
            bank_name="Test Bank",
            success_rate=0.95,
            avg_latency_ms=200
        )
        
        assert bank.get_effective_success_rate() == 0.95
        assert bank.get_effective_latency() == 200
    
    def test_degraded_bank_health(self):
        """Test degraded bank health."""
        bank = BankHealth(
            bank_name="Test Bank",
            success_rate=0.95,
            avg_latency_ms=200,
            is_degraded=True
        )
        
        # Success rate should be halved
        assert bank.get_effective_success_rate() == 0.95 * 0.5
        # Latency should be 3x
        assert bank.get_effective_latency() == 200 * 3
    
    def test_down_bank_health(self):
        """Test bank outage."""
        bank = BankHealth(
            bank_name="Test Bank",
            success_rate=0.95,
            avg_latency_ms=200,
            is_down=True
        )
        
        assert bank.get_effective_success_rate() == 0.0
        assert bank.get_effective_latency() == 30000  # Timeout

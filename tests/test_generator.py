"""
Tests for payment generator.
"""

import pytest
from datetime import datetime

from simulation.generator import PaymentGenerator
from simulation.models import PaymentMethod, PaymentStatus


class TestPaymentGenerator:
    """Test cases for PaymentGenerator."""
    
    def test_generator_initialization(self):
        """Test generator can be initialized."""
        generator = PaymentGenerator()
        assert generator is not None
        assert len(generator.bank_health) > 0
    
    def test_generator_with_config(self):
        """Test generator with configuration."""
        config = {
            "seed": 42,
            "base_failure_rate": 0.1,
            "base_latency_ms": 300
        }
        generator = PaymentGenerator(config=config)
        
        assert generator.base_failure_rate == 0.1
        assert generator.base_latency_ms == 300
    
    def test_generate_single_payment(self):
        """Test generating a single payment."""
        generator = PaymentGenerator()
        payment = generator.generate_payment()
        
        assert payment.payment_id is not None
        assert payment.amount > 0
        assert payment.bank in generator.BANKS
        assert payment.currency == "INR"
        assert payment.latency_ms > 0
    
    def test_generate_batch(self):
        """Test generating batch of payments."""
        generator = PaymentGenerator(config={"seed": 42})
        payments = generator.generate_batch(count=10, time_span_seconds=60)
        
        assert len(payments) == 10
        
        # Check all payments are valid
        for payment in payments:
            assert payment.payment_id is not None
            assert payment.amount > 0
    
    def test_force_failure(self):
        """Test forcing payment failure."""
        generator = PaymentGenerator()
        payment = generator.generate_payment(force_failure=True)
        
        assert payment.is_failed() is True
        assert payment.error_code.value != "NONE"
    
    def test_specific_payment_method(self):
        """Test generating payment with specific method."""
        generator = PaymentGenerator()
        payment = generator.generate_payment(payment_method=PaymentMethod.UPI)
        
        assert payment.payment_method == PaymentMethod.UPI
    
    def test_specific_bank(self):
        """Test generating payment for specific bank."""
        generator = PaymentGenerator()
        payment = generator.generate_payment(bank="HDFC Bank")
        
        assert payment.bank == "HDFC Bank"
    
    def test_bank_degradation(self):
        """Test bank degradation scenario."""
        generator = PaymentGenerator(config={"seed": 42})
        
        # Normal operation
        normal_payments = generator.generate_batch(count=20, time_span_seconds=10)
        normal_success_rate = sum(1 for p in normal_payments if p.is_successful()) / len(normal_payments)
        
        # Degrade bank
        generator.simulate_bank_degradation("HDFC Bank")
        
        # Generate more payments
        degraded_payments = [
            generator.generate_payment(bank="HDFC Bank")
            for _ in range(20)
        ]
        degraded_success_rate = sum(1 for p in degraded_payments if p.is_successful()) / len(degraded_payments)
        
        # Success rate should be lower during degradation
        assert degraded_success_rate < normal_success_rate
    
    def test_bank_outage(self):
        """Test bank outage scenario."""
        generator = PaymentGenerator()
        
        # Simulate outage
        generator.simulate_bank_outage("ICICI Bank")
        
        # Generate payments for that bank
        payments = [
            generator.generate_payment(bank="ICICI Bank")
            for _ in range(10)
        ]
        
        # All should fail
        success_count = sum(1 for p in payments if p.is_successful())
        assert success_count == 0
    
    def test_bank_restore(self):
        """Test restoring bank to normal."""
        generator = PaymentGenerator(config={"seed": 42})
        
        # Degrade bank
        generator.simulate_bank_degradation("Axis Bank")
        assert generator.bank_health["Axis Bank"].is_degraded is True
        
        # Restore bank
        generator.restore_bank("Axis Bank")
        assert generator.bank_health["Axis Bank"].is_degraded is False
    
    def test_retry_storm(self):
        """Test retry storm generation."""
        generator = PaymentGenerator()
        
        # Generate failed payment
        original = generator.generate_payment(force_failure=True)
        
        # Generate retries
        retries = generator.simulate_retry_storm(original, retry_count=3)
        
        assert len(retries) == 3
        
        # Check retry counts
        for i, retry in enumerate(retries, 1):
            assert retry.retry_count == i
            assert retry.payment_id == original.payment_id
    
    def test_bank_health_summary(self):
        """Test getting bank health summary."""
        generator = PaymentGenerator()
        
        summary = generator.get_bank_health_summary()
        
        assert len(summary) == len(generator.BANKS)
        
        for bank, health in summary.items():
            assert "success_rate" in health
            assert "avg_latency_ms" in health
            assert "is_degraded" in health
            assert "is_down" in health

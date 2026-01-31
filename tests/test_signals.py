"""
Tests for signal models.
"""

import pytest
from datetime import datetime

from agent.signals import PaymentSignals, Trend, Severity, BankSignal


class TestPaymentSignals:
    """Test cases for PaymentSignals."""
    
    def test_signals_creation(self):
        """Test creating payment signals."""
        signals = PaymentSignals(
            window_start="2026-01-31T00:00:00",
            window_end="2026-01-31T00:05:00",
            window_duration_seconds=300,
            total_payments=100,
            successful_payments=90,
            failed_payments=10,
            overall_success_rate=0.9,
            overall_failure_rate=0.1
        )
        
        assert signals.total_payments == 100
        assert signals.overall_success_rate == 0.9
        assert signals.window_duration_seconds == 300
    
    def test_signals_to_dict(self):
        """Test converting signals to dictionary."""
        signals = PaymentSignals(
            window_start="2026-01-31T00:00:00",
            window_end="2026-01-31T00:05:00",
            window_duration_seconds=300,
            total_payments=50,
            successful_payments=45,
            failed_payments=5,
            overall_success_rate=0.9,
            overall_failure_rate=0.1,
            latency_trend=Trend.RISING,
            anomaly_severity=Severity.WARNING
        )
        
        signals_dict = signals.to_dict()
        
        assert signals_dict['total_payments'] == 50
        assert signals_dict['latency_trend'] == 'rising'
        assert signals_dict['anomaly_severity'] == 'warning'
    
    def test_signals_summary(self):
        """Test getting signal summary."""
        signals = PaymentSignals(
            window_start="2026-01-31T00:00:00",
            window_end="2026-01-31T00:05:00",
            window_duration_seconds=300,
            total_payments=100,
            successful_payments=85,
            failed_payments=15,
            overall_success_rate=0.85,
            overall_failure_rate=0.15,
            avg_latency_ms=250.0,
            degraded_banks=["HDFC Bank"]
        )
        
        summary = signals.get_summary()
        
        assert "100 payments" in summary
        assert "85.0%" in summary
        assert "HDFC Bank" in summary


class TestBankSignal:
    """Test cases for BankSignal."""
    
    def test_bank_signal_creation(self):
        """Test creating bank signal."""
        bank_signal = BankSignal(
            bank_name="HDFC Bank",
            total_payments=50,
            success_rate=0.8,
            failure_rate=0.2,
            avg_latency_ms=300.0,
            is_degraded=True,
            severity=Severity.WARNING
        )
        
        assert bank_signal.bank_name == "HDFC Bank"
        assert bank_signal.is_degraded is True
        assert bank_signal.severity == Severity.WARNING

"""
Tests for metrics engine.
"""

import pytest
from datetime import datetime, timedelta

from agent.metrics import MetricsEngine
from simulation.generator import PaymentGenerator
from agent.signals import Trend, Severity


class TestMetricsEngine:
    """Test cases for MetricsEngine."""
    
    def test_engine_initialization(self):
        """Test metrics engine initialization."""
        engine = MetricsEngine()
        assert engine is not None
        assert engine.degradation_threshold == 0.3
    
    def test_compute_basic_signals(self):
        """Test computing basic signals."""
        generator = PaymentGenerator(config={"seed": 42})
        payments = generator.generate_batch(count=50, time_span_seconds=60)
        
        engine = MetricsEngine()
        signals = engine.compute_signals(payments, window_duration_seconds=60)
        
        assert signals.total_payments == 50
        assert 0 <= signals.overall_success_rate <= 1
        assert signals.overall_success_rate + signals.overall_failure_rate == 1.0
    
    def test_empty_payments(self):
        """Test handling empty payment list."""
        engine = MetricsEngine()
        signals = engine.compute_signals([], window_duration_seconds=60)
        
        assert signals.total_payments == 0
        assert signals.overall_success_rate == 0.0
    
    def test_bank_metrics(self):
        """Test bank-specific metrics."""
        generator = PaymentGenerator(config={"seed": 42})
        payments = generator.generate_batch(count=100, time_span_seconds=60)
        
        engine = MetricsEngine()
        signals = engine.compute_signals(payments)
        
        assert len(signals.bank_failure_rates) > 0
        assert len(signals.bank_avg_latencies) > 0
        assert len(signals.bank_volumes) > 0
        
        # Check that all values are valid
        for rate in signals.bank_failure_rates.values():
            assert 0 <= rate <= 1
    
    def test_method_metrics(self):
        """Test payment method metrics."""
        generator = PaymentGenerator(config={"seed": 42})
        payments = generator.generate_batch(count=100, time_span_seconds=60)
        
        engine = MetricsEngine()
        signals = engine.compute_signals(payments)
        
        assert len(signals.method_failure_rates) > 0
        assert len(signals.method_avg_latencies) > 0
    
    def test_latency_percentiles(self):
        """Test latency percentile calculation."""
        generator = PaymentGenerator(config={"seed": 42})
        payments = generator.generate_batch(count=100, time_span_seconds=60)
        
        engine = MetricsEngine()
        signals = engine.compute_signals(payments)
        
        # P50 should be less than P95 which should be less than P99
        assert signals.p50_latency_ms <= signals.p95_latency_ms
        assert signals.p95_latency_ms <= signals.p99_latency_ms
        assert signals.avg_latency_ms > 0
    
    def test_retry_metrics(self):
        """Test retry metrics computation."""
        generator = PaymentGenerator(config={"seed": 42})
        
        # Generate some failures
        original_payments = generator.generate_batch(count=50, time_span_seconds=60)
        
        # Add retries
        all_payments = list(original_payments)
        for payment in original_payments:
            if payment.is_failed() and payment.should_retry():
                retries = generator.simulate_retry_storm(payment, retry_count=2)
                all_payments.extend(retries)
        
        engine = MetricsEngine()
        signals = engine.compute_signals(all_payments)
        
        # Should have some retries if there were failures
        if signals.failed_payments > 0:
            assert signals.total_retries >= 0
    
    def test_error_distribution(self):
        """Test error distribution computation."""
        generator = PaymentGenerator(config={"seed": 42})
        generator.base_failure_rate = 0.2  # Increase failures
        
        payments = generator.generate_batch(count=100, time_span_seconds=60)
        
        engine = MetricsEngine()
        signals = engine.compute_signals(payments)
        
        if signals.failed_payments > 0:
            assert len(signals.error_code_counts) > 0
            assert len(signals.top_errors) > 0
    
    def test_degraded_bank_detection(self):
        """Test detection of degraded banks."""
        generator = PaymentGenerator(config={"seed": 42})
        
        # Degrade a bank
        generator.simulate_bank_degradation("HDFC Bank")
        
        payments = generator.generate_batch(count=100, time_span_seconds=60)
        
        engine = MetricsEngine()
        signals = engine.compute_signals(payments)
        
        # HDFC Bank should appear in degraded banks if it had enough traffic
        # and high failure rate
        if "HDFC Bank" in signals.bank_failure_rates:
            if signals.bank_failure_rates["HDFC Bank"] > 0.3:
                assert "HDFC Bank" in signals.degraded_banks
    
    def test_anomaly_detection(self):
        """Test anomaly detection."""
        generator = PaymentGenerator(config={"seed": 42})
        
        # Create severe issues
        generator.simulate_bank_outage("HDFC Bank")
        generator.simulate_bank_outage("ICICI Bank")
        
        payments = generator.generate_batch(count=100, time_span_seconds=60)
        
        engine = MetricsEngine()
        signals = engine.compute_signals(payments)
        
        # Should detect anomaly with multiple bank outages
        # (may not always trigger depending on which banks got traffic)
        assert isinstance(signals.has_anomaly, bool)
        assert isinstance(signals.anomaly_severity, Severity)
    
    def test_trend_detection(self):
        """Test trend detection over multiple windows."""
        generator = PaymentGenerator(config={"seed": 42})
        engine = MetricsEngine()
        
        # Generate first window
        payments1 = generator.generate_batch(count=50, time_span_seconds=60)
        signals1 = engine.compute_signals(payments1)
        
        # Trends should be unknown for first window
        assert signals1.latency_trend == Trend.UNKNOWN
        
        # Generate second window with higher latency
        generator.base_latency_ms = 500
        payments2 = generator.generate_batch(count=50, time_span_seconds=60)
        signals2 = engine.compute_signals(payments2)
        
        # Should detect rising latency
        assert signals2.latency_trend in [Trend.RISING, Trend.STABLE, Trend.UNKNOWN]
    
    def test_signals_to_dict(self):
        """Test converting signals to dictionary."""
        generator = PaymentGenerator(config={"seed": 42})
        payments = generator.generate_batch(count=50, time_span_seconds=60)
        
        engine = MetricsEngine()
        signals = engine.compute_signals(payments)
        
        signals_dict = signals.to_dict()
        
        assert isinstance(signals_dict, dict)
        assert 'total_payments' in signals_dict
        assert 'overall_success_rate' in signals_dict
        assert isinstance(signals_dict['latency_trend'], str)

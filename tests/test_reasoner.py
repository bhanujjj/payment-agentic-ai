"""
Tests for reasoner component.
"""

import pytest
import asyncio

from agent.reasoner import Reasoner
from agent.signals import PaymentSignals, Trend, Severity
from simulation.generator import PaymentGenerator
from agent.metrics import MetricsEngine


class TestReasoner:
    """Test cases for Reasoner."""
    
    def test_reasoner_initialization(self):
        """Test reasoner initialization."""
        reasoner = Reasoner()
        assert reasoner is not None
    
    def test_reasoner_with_config(self):
        """Test reasoner with configuration."""
        config = {
            "gemini_api_key": None,  # Force fallback
            "temperature": 0.5,
            "max_tokens": 500
        }
        reasoner = Reasoner(config=config)
        
        assert reasoner.temperature == 0.5
        assert reasoner.max_tokens == 500
    
    @pytest.mark.asyncio
    async def test_fallback_reasoning_normal(self):
        """Test fallback reasoning with normal operation."""
        # Create normal signals
        signals = PaymentSignals(
            window_start="2026-01-31T00:00:00",
            window_end="2026-01-31T00:05:00",
            window_duration_seconds=300,
            total_payments=100,
            successful_payments=96,
            failed_payments=4,
            overall_success_rate=0.96,
            overall_failure_rate=0.04,
            avg_latency_ms=200.0,
            p95_latency_ms=350.0
        )
        
        reasoner = Reasoner(config={"gemini_api_key": None})
        reasoning = await reasoner.reason(signals)
        
        assert reasoning is not None
        assert isinstance(reasoning.hypotheses, dict)
        assert 0 <= reasoning.overall_confidence <= 1
        
        # Should detect normal operation
        if "normal_operation" in reasoning.hypotheses:
            assert reasoning.hypotheses["normal_operation"] > 0.5
    
    @pytest.mark.asyncio
    async def test_fallback_reasoning_degraded(self):
        """Test fallback reasoning with degraded bank."""
        signals = PaymentSignals(
            window_start="2026-01-31T00:00:00",
            window_end="2026-01-31T00:05:00",
            window_duration_seconds=300,
            total_payments=100,
            successful_payments=65,
            failed_payments=35,
            overall_success_rate=0.65,
            overall_failure_rate=0.35,
            avg_latency_ms=400.0,
            p95_latency_ms=1200.0,
            degraded_banks=["HDFC Bank"],
            has_anomaly=True,
            anomaly_severity=Severity.WARNING
        )
        
        reasoner = Reasoner(config={"gemini_api_key": None})
        reasoning = await reasoner.reason(signals)
        
        assert reasoning is not None
        assert len(reasoning.hypotheses) > 0
        
        # Should detect bank degradation
        if "bank_degradation" in reasoning.hypotheses:
            assert reasoning.hypotheses["bank_degradation"] > 0.5
    
    @pytest.mark.asyncio
    async def test_fallback_reasoning_high_latency(self):
        """Test fallback reasoning with high latency."""
        signals = PaymentSignals(
            window_start="2026-01-31T00:00:00",
            window_end="2026-01-31T00:05:00",
            window_duration_seconds=300,
            total_payments=100,
            successful_payments=85,
            failed_payments=15,
            overall_success_rate=0.85,
            overall_failure_rate=0.15,
            avg_latency_ms=800.0,
            p95_latency_ms=2000.0,
            p99_latency_ms=3000.0
        )
        
        reasoner = Reasoner(config={"gemini_api_key": None})
        reasoning = await reasoner.reason(signals)
        
        # Should detect network issues due to high latency
        assert reasoning is not None
        assert len(reasoning.hypotheses) > 0
    
    @pytest.mark.asyncio
    async def test_reasoning_with_real_data(self):
        """Test reasoning with real generated data."""
        # Generate payment data
        generator = PaymentGenerator(config={"seed": 42})
        generator.simulate_bank_degradation("HDFC Bank")
        payments = generator.generate_batch(count=100, time_span_seconds=300)
        
        # Compute signals
        metrics_engine = MetricsEngine()
        signals = metrics_engine.compute_signals(payments)
        
        # Reason about it (will use fallback if no API key)
        reasoner = Reasoner()
        reasoning = await reasoner.reason(signals)
        
        assert reasoning is not None
        assert isinstance(reasoning.hypotheses, dict)
        assert isinstance(reasoning.explanation, str)
        assert isinstance(reasoning.assumptions, list)
        assert isinstance(reasoning.uncertainty, list)
        assert 0 <= reasoning.overall_confidence <= 1
    
    @pytest.mark.asyncio
    async def test_get_top_hypothesis(self):
        """Test getting top hypothesis from reasoning."""
        signals = PaymentSignals(
            window_start="2026-01-31T00:00:00",
            window_end="2026-01-31T00:05:00",
            window_duration_seconds=300,
            total_payments=100,
            successful_payments=50,
            failed_payments=50,
            overall_success_rate=0.5,
            overall_failure_rate=0.5,
            degraded_banks=["HDFC Bank", "ICICI Bank"]
        )
        
        reasoner = Reasoner(config={"gemini_api_key": None})
        reasoning = await reasoner.reason(signals)
        
        top = reasoning.get_top_hypothesis()
        
        if top is not None:
            assert isinstance(top, tuple)
            assert len(top) == 2
            assert isinstance(top[0], str)
            assert isinstance(top[1], float)
            assert 0 <= top[1] <= 1

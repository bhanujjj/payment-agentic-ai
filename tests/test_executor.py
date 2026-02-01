"""
Tests for action executor.
"""

import pytest
from datetime import datetime

from simulation.generator import PaymentGenerator
from agent.metrics import MetricsEngine
from agent.executor import ActionExecutor
from agent.execution_models import ExecutionStatus, SystemState
from agent.decision_models import Decision, RiskLevel
from agent.reasoner import Reasoner
from agent.decider import DecisionEngine


class TestActionExecutor:
    """Test suite for ActionExecutor."""
    
    def test_executor_initialization(self):
        """Test executor initializes correctly."""
        executor = ActionExecutor()
        assert executor.system_state is not None
        assert isinstance(executor.system_state, SystemState)
    
    def test_do_nothing_execution(self):
        """Test do_nothing action executes."""
        # Generate real signals
        gen = PaymentGenerator(config={'seed': 42})
        payments = gen.generate_batch(count=100, time_span_seconds=300)
        engine = MetricsEngine()
        signals = engine.compute_signals(payments)
        
        executor = ActionExecutor()
        
        decision = Decision(
            selected_action="do_nothing",
            confidence=0.9,
            risk_level=RiskLevel.LOW,
            requires_human_approval=False,
            reasoning_summary="System healthy",
            considered_actions=[],
            rejected_actions=[]
        )
        
        result = executor.execute(decision, signals)
        
        assert result.executed is True
        assert result.status == ExecutionStatus.EXECUTED
        assert result.action == "do_nothing"
        assert result.impact_scope == "none"
    
    def test_alert_ops_execution(self):
        """Test alert_ops action executes."""
        # Generate degraded scenario
        gen = PaymentGenerator(config={'seed': 42})
        gen.simulate_bank_degradation('HDFC Bank')
        payments = gen.generate_batch(count=100, time_span_seconds=300)
        engine = MetricsEngine()
        signals = engine.compute_signals(payments)
        
        executor = ActionExecutor()
        
        decision = Decision(
            selected_action="alert_ops",
            confidence=0.8,
            risk_level=RiskLevel.LOW,
            requires_human_approval=False,
            reasoning_summary="Bank degradation detected",
            considered_actions=[],
            rejected_actions=[]
        )
        
        result = executor.execute(decision, signals)
        
        assert result.executed is True
        assert result.status == ExecutionStatus.EXECUTED
        assert result.action == "alert_ops"
        assert len(executor.system_state.alerts) > 0
    
    def test_path_suppression_execution(self):
        """Test path suppression executes."""
        # Generate degraded scenario
        gen = PaymentGenerator(config={'seed': 42})
        gen.simulate_bank_degradation('HDFC Bank')
        gen.simulate_bank_degradation('ICICI Bank')
        payments = gen.generate_batch(count=100, time_span_seconds=300)
        engine = MetricsEngine()
        signals = engine.compute_signals(payments)
        
        executor = ActionExecutor()
        
        decision = Decision(
            selected_action="recommend_path_suppression",
            confidence=0.75,
            risk_level=RiskLevel.MEDIUM,
            requires_human_approval=False,
            reasoning_summary="Suppress degraded paths",
            considered_actions=[],
            rejected_actions=[]
        )
        
        result = executor.execute(decision, signals)
        
        assert result.executed is True
        assert result.status == ExecutionStatus.EXECUTED
        assert result.action == "recommend_path_suppression"
        assert len(executor.system_state.routing_overrides) > 0
    
    def test_approval_blocking(self):
        """Test that high-risk actions are blocked for approval."""
        # Generate critical scenario
        gen = PaymentGenerator(config={'seed': 42})
        gen.simulate_bank_outage('HDFC Bank')
        gen.simulate_bank_outage('ICICI Bank')
        payments = gen.generate_batch(count=100, time_span_seconds=300)
        engine = MetricsEngine()
        signals = engine.compute_signals(payments)
        
        executor = ActionExecutor()
        
        decision = Decision(
            selected_action="recommend_path_suppression",
            confidence=0.72,
            risk_level=RiskLevel.MEDIUM,
            requires_human_approval=True,  # Requires approval
            reasoning_summary="High risk action",
            considered_actions=[],
            rejected_actions=[]
        )
        
        result = executor.execute(decision, signals)
        
        assert result.executed is False
        assert result.status == ExecutionStatus.PENDING_HUMAN_APPROVAL
    
    def test_circuit_breaker_execution(self):
        """Test circuit breaker action."""
        # Generate degraded scenario
        gen = PaymentGenerator(config={'seed': 42})
        gen.simulate_bank_degradation('HDFC Bank')
        payments = gen.generate_batch(count=100, time_span_seconds=300)
        engine = MetricsEngine()
        signals = engine.compute_signals(payments)
        
        executor = ActionExecutor()
        
        decision = Decision(
            selected_action="recommend_circuit_breaker",
            confidence=0.78,
            risk_level=RiskLevel.MEDIUM,
            requires_human_approval=False,
            reasoning_summary="Enable circuit breakers",
            considered_actions=[],
            rejected_actions=[]
        )
        
        result = executor.execute(decision, signals)
        
        assert result.executed is True
        assert result.status == ExecutionStatus.EXECUTED
        assert len(executor.system_state.circuit_breakers) > 0
    
    def test_retry_adjustment_execution(self):
        """Test retry adjustment action."""
        # Generate normal scenario with retries
        gen = PaymentGenerator(config={'seed': 42})
        payments = gen.generate_batch(count=100, time_span_seconds=300)
        engine = MetricsEngine()
        signals = engine.compute_signals(payments)
        
        executor = ActionExecutor()
        
        decision = Decision(
            selected_action="recommend_retry_adjustment",
            confidence=0.82,
            risk_level=RiskLevel.LOW,
            requires_human_approval=False,
            reasoning_summary="Adjust retry policy",
            considered_actions=[],
            rejected_actions=[]
        )
        
        result = executor.execute(decision, signals)
        
        assert result.executed is True
        assert result.status == ExecutionStatus.EXECUTED
        assert "max_retries" in executor.system_state.retry_policy
    
    def test_state_reset(self):
        """Test state can be reset."""
        executor = ActionExecutor()
        
        # Make some changes
        executor.system_state.routing_overrides["HDFC Bank"] = "suppressed"
        executor.system_state.alerts.append("Test alert")
        executor.system_state.circuit_breakers["ICICI Bank"] = True
        
        # Reset
        executor.reset_state()
        
        assert len(executor.system_state.routing_overrides) == 0
        assert len(executor.system_state.alerts) == 0
        assert len(executor.system_state.circuit_breakers) == 0
    
    def test_unknown_action(self):
        """Test handling of unknown action."""
        # Generate normal scenario
        gen = PaymentGenerator(config={'seed': 42})
        payments = gen.generate_batch(count=100, time_span_seconds=300)
        engine = MetricsEngine()
        signals = engine.compute_signals(payments)
        
        executor = ActionExecutor()
        
        decision = Decision(
            selected_action="unknown_action",
            confidence=0.5,
            risk_level=RiskLevel.LOW,
            requires_human_approval=False,
            reasoning_summary="Unknown",
            considered_actions=[],
            rejected_actions=[]
        )
        
        result = executor.execute(decision, signals)
        
        assert result.executed is False
        assert result.status == ExecutionStatus.BLOCKED
        assert result.error is not None

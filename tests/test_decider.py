"""
Tests for decision engine.
"""

import pytest
from simulation import PaymentGenerator
from agent import (
    MetricsEngine, Reasoner, DecisionEngine,
    ReasoningResult, DecisionConstraints, RiskLevel
)


class TestDecisionEngine:
    """Tests for DecisionEngine."""
    
    def test_decision_engine_initialization(self):
        """Test creating a decision engine."""
        engine = DecisionEngine()
        assert engine is not None
        assert engine.constraints is not None
    
    def test_decision_engine_with_custom_constraints(self):
        """Test creating engine with custom constraints."""
        constraints = DecisionConstraints(
            max_auto_approve_risk=RiskLevel.MEDIUM,
            min_confidence_for_action=0.7
        )
        engine = DecisionEngine(constraints=constraints)
        
        assert engine.constraints.max_auto_approve_risk == RiskLevel.MEDIUM
        assert engine.constraints.min_confidence_for_action == 0.7
    
    def test_decide_with_normal_operation(self):
        """Test decision making for normal operation."""
        # Generate normal data
        gen = PaymentGenerator(config={'seed': 42})
        gen.base_failure_rate = 0.02
        payments = gen.generate_batch(count=100, time_span_seconds=300)
        
        # Compute signals
        metrics_engine = MetricsEngine()
        signals = metrics_engine.compute_signals(payments)
        
        # Create reasoning (simulated)
        reasoning = ReasoningResult(
            hypotheses={"normal_operation": 0.9},
            explanation="System operating normally",
            assumptions=["Normal traffic"],
            uncertainty=[],
            overall_confidence=0.85
        )
        
        # Make decision
        engine = DecisionEngine()
        decision = engine.decide(reasoning, signals)
        
        assert decision is not None
        assert decision.selected_action in ["do_nothing", "alert_ops"]
        assert decision.confidence > 0
        assert decision.risk_level in [RiskLevel.LOW, RiskLevel.MEDIUM]
    
    def test_decide_with_bank_degradation(self):
        """Test decision making for bank degradation."""
        # Generate degraded data
        gen = PaymentGenerator(config={'seed': 42})
        gen.simulate_bank_degradation("HDFC Bank")
        payments = gen.generate_batch(count=200, time_span_seconds=300)
        
        # Compute signals
        metrics_engine = MetricsEngine()
        signals = metrics_engine.compute_signals(payments)
        
        # Create reasoning
        reasoning = ReasoningResult(
            hypotheses={"bank_degradation": 0.85, "network_issues": 0.4},
            explanation="HDFC Bank degraded",
            assumptions=["Bank is primary cause"],
            uncertainty=["Duration unknown"],
            overall_confidence=0.8
        )
        
        # Make decision with constraints that allow MEDIUM risk
        constraints = DecisionConstraints(max_auto_approve_risk=RiskLevel.MEDIUM)
        engine = DecisionEngine(constraints=constraints)
        decision = engine.decide(reasoning, signals)
        
        assert decision is not None
        assert len(decision.considered_actions) > 0
        
        # Should consider rerouting or path suppression
        action_names = [a.action for a in decision.considered_actions]
        assert any("reroute" in a or "suppression" in a for a in action_names)
    
    def test_high_risk_requires_approval(self):
        """Test that high risk actions require approval."""
        gen = PaymentGenerator(config={'seed': 42})
        payments = gen.generate_batch(count=100, time_span_seconds=300)
        
        metrics_engine = MetricsEngine()
        signals = metrics_engine.compute_signals(payments)
        
        reasoning = ReasoningResult(
            hypotheses={"bank_outage": 0.9},
            explanation="Critical outage",
            assumptions=[],
            uncertainty=[],
            overall_confidence=0.9
        )
        
        # Engine with strict constraints
        constraints = DecisionConstraints(max_auto_approve_risk=RiskLevel.LOW)
        engine = DecisionEngine(constraints=constraints)
        decision = engine.decide(reasoning, signals)
        
        # Medium or high risk actions should require approval
        if decision.risk_level in [RiskLevel.MEDIUM, RiskLevel.HIGH]:
            assert decision.requires_human_approval
    
    def test_decision_respects_constraints(self):
        """Test that decisions respect constraints."""
        gen = PaymentGenerator(config={'seed': 42})
        gen.simulate_bank_degradation("HDFC Bank")
        payments = gen.generate_batch(count=200, time_span_seconds=300)
        
        metrics_engine = MetricsEngine()
        signals = metrics_engine.compute_signals(payments)
        
        reasoning = ReasoningResult(
            hypotheses={"bank_degradation": 0.8},
            explanation="Bank degraded",
            assumptions=[],
            uncertainty=[],
            overall_confidence=0.75
        )
        
        # Disable rerouting
        constraints = DecisionConstraints(allow_rerouting=False)
        engine = DecisionEngine(constraints=constraints)
        decision = engine.decide(reasoning, signals)
        
        # Should not select reroute
        assert decision.selected_action != "recommend_reroute"
    
    def test_decision_to_dict(self):
        """Test converting decision to dict."""
        gen = PaymentGenerator(config={'seed': 42})
        payments = gen.generate_batch(count=100, time_span_seconds=300)
        
        metrics_engine = MetricsEngine()
        signals = metrics_engine.compute_signals(payments)
        
        reasoning = ReasoningResult(
            hypotheses={"normal_operation": 0.85},
            explanation="Normal",
            assumptions=[],
            uncertainty=[],
            overall_confidence=0.8
        )
        
        engine = DecisionEngine()
        decision = engine.decide(reasoning, signals)
        
        data = decision.to_dict()
        
        assert 'selected_action' in data
        assert 'confidence' in data
        assert 'risk_level' in data
        assert 'requires_human_approval' in data
        assert 'considered_actions' in data
        assert isinstance(data['considered_actions'], list)

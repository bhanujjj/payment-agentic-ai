"""
Tests for decision models.
"""

import pytest
from agent.decision_models import (
    Decision, ActionScore, ActionType, RiskLevel, DecisionConstraints
)


class TestActionScore:
    """Tests for ActionScore model."""
    
    def test_action_score_creation(self):
        """Test creating an action score."""
        score = ActionScore(
            action="test_action",
            score=0.75,
            expected_success_rate_impact=0.2,
            risk_level=RiskLevel.MEDIUM
        )
        
        assert score.action == "test_action"
        assert score.score == 0.75
        assert score.expected_success_rate_impact == 0.2
        assert score.risk_level == RiskLevel.MEDIUM
    
    def test_action_score_to_dict(self):
        """Test converting action score to dict."""
        score = ActionScore(
            action="test_action",
            score=0.75,
            risk_level=RiskLevel.HIGH
        )
        
        data = score.to_dict()
        assert data['action'] == "test_action"
        assert data['score'] == 0.75
        assert data['risk_level'] == "HIGH"


class TestDecision:
    """Tests for Decision model."""
    
    def test_decision_creation(self):
        """Test creating a decision."""
        decision = Decision(
            selected_action="alert_ops",
            confidence=0.8,
            risk_level=RiskLevel.LOW,
            requires_human_approval=False,
            reasoning_summary="Test reasoning"
        )
        
        assert decision.selected_action == "alert_ops"
        assert decision.confidence == 0.8
        assert decision.risk_level == RiskLevel.LOW
        assert not decision.requires_human_approval
    
    def test_decision_to_dict(self):
        """Test converting decision to dict."""
        action1 = ActionScore(action="action1", score=0.8)
        action2 = ActionScore(action="action2", score=0.6)
        
        decision = Decision(
            selected_action="action1",
            confidence=0.8,
            risk_level=RiskLevel.MEDIUM,
            requires_human_approval=True,
            reasoning_summary="Test",
            considered_actions=[action1, action2]
        )
        
        data = decision.to_dict()
        assert data['selected_action'] == "action1"
        assert data['confidence'] == 0.8
        assert data['risk_level'] == "MEDIUM"
        assert data['requires_human_approval'] is True
        assert len(data['considered_actions']) == 2
        assert data['considered_actions'][0]['action'] == "action1"
    
    def test_decision_get_summary(self):
        """Test getting decision summary."""
        decision = Decision(
            selected_action="alert_ops",
            confidence=0.75,
            risk_level=RiskLevel.LOW,
            requires_human_approval=False,
            reasoning_summary="Test reasoning"
        )
        
        summary = decision.get_summary()
        assert "alert_ops" in summary
        assert "75%" in summary
        assert "LOW" in summary


class TestActionType:
    """Tests for ActionType enum."""
    
    def test_action_types_exist(self):
        """Test that all action types are defined."""
        assert ActionType.DO_NOTHING.value == "do_nothing"
        assert ActionType.ALERT_OPS.value == "alert_ops"
        assert ActionType.RECOMMEND_REROUTE.value == "recommend_reroute"
        assert ActionType.RECOMMEND_RETRY_REDUCTION.value == "recommend_retry_reduction"
        assert ActionType.RECOMMEND_PATH_SUPPRESSION.value == "recommend_path_suppression"


class TestRiskLevel:
    """Tests for RiskLevel enum."""
    
    def test_risk_levels_exist(self):
        """Test that all risk levels are defined."""
        assert RiskLevel.LOW.value == "LOW"
        assert RiskLevel.MEDIUM.value == "MEDIUM"
        assert RiskLevel.HIGH.value == "HIGH"
        assert RiskLevel.CRITICAL.value == "CRITICAL"


class TestDecisionConstraints:
    """Tests for DecisionConstraints."""
    
    def test_default_constraints(self):
        """Test default constraint values."""
        constraints = DecisionConstraints()
        
        assert constraints.max_auto_approve_risk == RiskLevel.LOW
        assert constraints.min_confidence_for_action == 0.5
        assert constraints.allow_rerouting is True
    
    def test_custom_constraints(self):
        """Test custom constraint values."""
        constraints = DecisionConstraints(
            max_auto_approve_risk=RiskLevel.MEDIUM,
            min_confidence_for_action=0.7,
            allow_rerouting=False
        )
        
        assert constraints.max_auto_approve_risk == RiskLevel.MEDIUM
        assert constraints.min_confidence_for_action == 0.7
        assert constraints.allow_rerouting is False
    
    def test_constraints_to_dict(self):
        """Test converting constraints to dict."""
        constraints = DecisionConstraints()
        data = constraints.to_dict()
        
        assert data['max_auto_approve_risk'] == "LOW"
        assert data['min_confidence_for_action'] == 0.5

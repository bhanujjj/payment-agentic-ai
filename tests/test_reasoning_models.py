"""
Tests for reasoning models.
"""

import pytest

from agent.reasoning_models import ReasoningResult, HypothesisType


class TestReasoningResult:
    """Test cases for ReasoningResult."""
    
    def test_reasoning_result_creation(self):
        """Test creating reasoning result."""
        result = ReasoningResult(
            hypotheses={
                "bank_degradation": 0.8,
                "network_issues": 0.6
            },
            explanation="Bank appears degraded",
            assumptions=["Assuming normal traffic patterns"],
            uncertainty=["Unclear if issue is temporary"],
            overall_confidence=0.75
        )
        
        assert result.hypotheses["bank_degradation"] == 0.8
        assert result.overall_confidence == 0.75
        assert len(result.assumptions) == 1
    
    def test_get_top_hypothesis(self):
        """Test getting top hypothesis."""
        result = ReasoningResult(
            hypotheses={
                "bank_degradation": 0.8,
                "network_issues": 0.6,
                "normal_operation": 0.3
            }
        )
        
        top = result.get_top_hypothesis()
        
        assert top is not None
        assert top[0] == "bank_degradation"
        assert top[1] == 0.8
    
    def test_get_top_hypothesis_empty(self):
        """Test getting top hypothesis with no hypotheses."""
        result = ReasoningResult()
        
        top = result.get_top_hypothesis()
        
        assert top is None
    
    def test_to_dict(self):
        """Test converting to dictionary."""
        result = ReasoningResult(
            hypotheses={"bank_degradation": 0.8},
            explanation="Test explanation",
            overall_confidence=0.7
        )
        
        result_dict = result.to_dict()
        
        assert isinstance(result_dict, dict)
        assert result_dict["hypotheses"]["bank_degradation"] == 0.8
        assert result_dict["explanation"] == "Test explanation"
    
    def test_get_summary(self):
        """Test getting summary."""
        result = ReasoningResult(
            hypotheses={
                "bank_degradation": 0.85,
                "network_issues": 0.6
            },
            explanation="System experiencing issues",
            overall_confidence=0.75
        )
        
        summary = result.get_summary()
        
        assert "bank_degradation" in summary
        assert "85%" in summary
        assert "75%" in summary


class TestHypothesisType:
    """Test cases for HypothesisType."""
    
    def test_hypothesis_types_exist(self):
        """Test that hypothesis types are defined."""
        assert hasattr(HypothesisType, 'BANK_DEGRADATION')
        assert hasattr(HypothesisType, 'BANK_OUTAGE')
        assert hasattr(HypothesisType, 'NETWORK_ISSUES')
        assert hasattr(HypothesisType, 'RETRY_STORM')
        assert hasattr(HypothesisType, 'NORMAL_OPERATION')

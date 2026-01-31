"""
Decision Engine - Deterministic decision making based on reasoning output.

This is the control layer that decides WHAT TO DO based on the agent's reasoning.

IMPORTANT: This layer does NOT use LLMs. It uses scoring and logic.
"""

import logging
from typing import Dict, List, Optional

from agent.reasoning_models import ReasoningResult
from agent.signals import PaymentSignals
from agent.decision_models import (
    Decision, ActionScore, ActionType, RiskLevel, DecisionConstraints
)


class DecisionEngine:
    """
    Makes decisions about what actions to take based on reasoning output.
    
    This is pure control logic - no LLMs, just scoring and constraints.
    """
    
    def __init__(self, constraints: Optional[DecisionConstraints] = None):
        """
        Initialize decision engine.
        
        Args:
            constraints: Decision constraints and guardrails
        """
        self.constraints = constraints or DecisionConstraints()
        self.logger = logging.getLogger(__name__)
    
    def decide(
        self,
        reasoning: ReasoningResult,
        signals: PaymentSignals
    ) -> Decision:
        """
        Make a decision based on reasoning and signals.
        
        Args:
            reasoning: Reasoning output from LLM
            signals: Current payment signals
            
        Returns:
            Decision with selected action and scores
        """
        self.logger.info("Starting decision process")
        
        # Generate candidate actions
        candidate_actions = self._generate_candidate_actions(reasoning, signals)
        
        # Score each action
        scored_actions = []
        for action in candidate_actions:
            score = self._score_action(action, reasoning, signals)
            scored_actions.append(score)
        
        # Apply constraints and select best action
        decision = self._select_best_action(scored_actions, reasoning)
        
        self.logger.info(f"Decision made: {decision.selected_action} (confidence: {decision.confidence:.0%})")
        
        return decision
    
    def _generate_candidate_actions(
        self,
        reasoning: ReasoningResult,
        signals: PaymentSignals
    ) -> List[str]:
        """
        Generate list of candidate actions based on context.
        
        Args:
            reasoning: Reasoning output
            signals: Payment signals
            
        Returns:
            List of action names
        """
        actions = [ActionType.DO_NOTHING.value, ActionType.ALERT_OPS.value]
        
        # Add actions based on hypotheses
        top_hypotheses = sorted(
            reasoning.hypotheses.items(),
            key=lambda x: x[1],
            reverse=True
        )[:3]
        
        for hypothesis, confidence in top_hypotheses:
            if confidence < 0.3:
                continue
            
            if "bank_degradation" in hypothesis or "bank_outage" in hypothesis:
                if self.constraints.allow_rerouting:
                    actions.append(ActionType.RECOMMEND_REROUTE.value)
                if self.constraints.allow_path_suppression:
                    actions.append(ActionType.RECOMMEND_PATH_SUPPRESSION.value)
            
            if "retry_storm" in hypothesis:
                actions.append(ActionType.RECOMMEND_RETRY_REDUCTION.value)
            
            if "network_issues" in hypothesis or "peak_load" in hypothesis:
                if self.constraints.allow_circuit_breaker:
                    actions.append(ActionType.RECOMMEND_CIRCUIT_BREAKER.value)
                actions.append(ActionType.RECOMMEND_RATE_LIMIT.value)
        
        # Remove duplicates while preserving order
        seen = set()
        unique_actions = []
        for action in actions:
            if action not in seen:
                seen.add(action)
                unique_actions.append(action)
        
        return unique_actions
    
    def _score_action(
        self,
        action: str,
        reasoning: ReasoningResult,
        signals: PaymentSignals
    ) -> ActionScore:
        """
        Score a single action.
        
        Args:
            action: Action name
            reasoning: Reasoning output
            signals: Payment signals
            
        Returns:
            Scored action
        """
        # Base score from reasoning confidence
        base_score = reasoning.overall_confidence
        
        # Calculate impact metrics
        success_impact = self._estimate_success_rate_impact(action, signals)
        latency_impact = self._estimate_latency_impact(action, signals)
        cost_impact = self._estimate_cost_impact(action)
        
        # Calculate risk level
        risk_level = self._assess_risk(action, success_impact, latency_impact, cost_impact)
        
        # Calculate reversibility
        reversibility = self._assess_reversibility(action)
        
        # Calculate final score
        score = self._calculate_final_score(
            base_score,
            success_impact,
            latency_impact,
            cost_impact,
            risk_level,
            reversibility
        )
        
        # Generate reasoning
        action_reasoning = self._generate_action_reasoning(
            action, success_impact, latency_impact, cost_impact, risk_level
        )
        
        return ActionScore(
            action=action,
            score=score,
            expected_success_rate_impact=success_impact,
            expected_latency_impact=latency_impact,
            expected_cost_impact=cost_impact,
            risk_level=risk_level,
            reversibility=reversibility,
            reasoning=action_reasoning
        )
    
    def _estimate_success_rate_impact(self, action: str, signals: PaymentSignals) -> float:
        """Estimate impact on success rate (-1 to 1)."""
        if action == ActionType.DO_NOTHING.value:
            return 0.0
        
        if action == ActionType.ALERT_OPS.value:
            return 0.0  # No direct impact
        
        if action == ActionType.RECOMMEND_REROUTE.value:
            # Rerouting can improve success rate if bank is degraded
            if signals.degraded_banks:
                return 0.3  # 30% improvement expected
            return 0.1
        
        if action == ActionType.RECOMMEND_PATH_SUPPRESSION.value:
            # Suppressing bad paths improves success rate
            return 0.2
        
        if action == ActionType.RECOMMEND_RETRY_REDUCTION.value:
            # Reducing retries may slightly lower success rate
            return -0.05
        
        if action == ActionType.RECOMMEND_CIRCUIT_BREAKER.value:
            # Circuit breaker prevents cascading failures
            return 0.15
        
        if action == ActionType.RECOMMEND_RATE_LIMIT.value:
            # Rate limiting may reduce success for some requests
            return -0.1
        
        return 0.0
    
    def _estimate_latency_impact(self, action: str, signals: PaymentSignals) -> float:
        """Estimate impact on latency (-1 to 1)."""
        if action == ActionType.DO_NOTHING.value:
            return 0.0
        
        if action == ActionType.ALERT_OPS.value:
            return 0.0
        
        if action == ActionType.RECOMMEND_REROUTE.value:
            # Rerouting may slightly increase latency
            return -0.1
        
        if action == ActionType.RECOMMEND_PATH_SUPPRESSION.value:
            # Suppressing slow paths improves latency
            return 0.2
        
        if action == ActionType.RECOMMEND_RETRY_REDUCTION.value:
            # Fewer retries = lower latency
            return 0.3
        
        if action == ActionType.RECOMMEND_CIRCUIT_BREAKER.value:
            # Circuit breaker prevents slow requests
            return 0.25
        
        if action == ActionType.RECOMMEND_RATE_LIMIT.value:
            # Rate limiting may increase latency for queued requests
            return -0.15
        
        return 0.0
    
    def _estimate_cost_impact(self, action: str) -> float:
        """Estimate cost impact (-1 to 1)."""
        if action == ActionType.DO_NOTHING.value:
            return 0.0
        
        if action == ActionType.ALERT_OPS.value:
            return -0.05  # Small ops cost
        
        if action == ActionType.RECOMMEND_REROUTE.value:
            return -0.2  # Rerouting has infrastructure cost
        
        if action == ActionType.RECOMMEND_PATH_SUPPRESSION.value:
            return 0.1  # Saves cost by avoiding bad paths
        
        if action == ActionType.RECOMMEND_RETRY_REDUCTION.value:
            return 0.15  # Saves retry costs
        
        if action == ActionType.RECOMMEND_CIRCUIT_BREAKER.value:
            return 0.05  # Small savings
        
        if action == ActionType.RECOMMEND_RATE_LIMIT.value:
            return 0.1  # Reduces load
        
        return 0.0
    
    def _assess_risk(
        self,
        action: str,
        success_impact: float,
        latency_impact: float,
        cost_impact: float
    ) -> RiskLevel:
        """Assess risk level of action."""
        if action == ActionType.DO_NOTHING.value:
            return RiskLevel.LOW
        
        if action == ActionType.ALERT_OPS.value:
            return RiskLevel.LOW
        
        # High risk if negative impacts exceed thresholds
        if success_impact < -self.constraints.max_allowed_success_rate_drop:
            return RiskLevel.HIGH
        
        if latency_impact < -self.constraints.max_allowed_latency_increase:
            return RiskLevel.HIGH
        
        if cost_impact < -self.constraints.max_allowed_cost_increase:
            return RiskLevel.HIGH
        
        # Medium risk for infrastructure changes
        if action in [
            ActionType.RECOMMEND_REROUTE.value,
            ActionType.RECOMMEND_PATH_SUPPRESSION.value,
            ActionType.RECOMMEND_CIRCUIT_BREAKER.value
        ]:
            return RiskLevel.MEDIUM
        
        return RiskLevel.LOW
    
    def _assess_reversibility(self, action: str) -> float:
        """Assess how easily action can be reversed (0-1)."""
        if action == ActionType.DO_NOTHING.value:
            return 1.0
        
        if action == ActionType.ALERT_OPS.value:
            return 1.0
        
        if action == ActionType.RECOMMEND_REROUTE.value:
            return 0.8  # Can reroute back
        
        if action == ActionType.RECOMMEND_PATH_SUPPRESSION.value:
            return 0.9  # Can unsuppress
        
        if action == ActionType.RECOMMEND_RETRY_REDUCTION.value:
            return 0.95  # Easy to adjust retry config
        
        if action == ActionType.RECOMMEND_CIRCUIT_BREAKER.value:
            return 0.85  # Can disable circuit breaker
        
        if action == ActionType.RECOMMEND_RATE_LIMIT.value:
            return 0.9  # Can adjust limits
        
        return 0.5
    
    def _calculate_final_score(
        self,
        base_score: float,
        success_impact: float,
        latency_impact: float,
        cost_impact: float,
        risk_level: RiskLevel,
        reversibility: float
    ) -> float:
        """Calculate final action score."""
        # Weight factors
        success_weight = 0.4
        latency_weight = 0.3
        cost_weight = 0.1
        reversibility_weight = 0.2
        
        # Normalize impacts to 0-1 range
        success_score = (success_impact + 1) / 2
        latency_score = (latency_impact + 1) / 2
        cost_score = (cost_impact + 1) / 2
        
        # Calculate weighted score
        score = (
            base_score * 0.3 +  # Base from reasoning confidence
            success_score * success_weight +
            latency_score * latency_weight +
            cost_score * cost_weight +
            reversibility * reversibility_weight
        )
        
        # Apply risk penalty
        if risk_level == RiskLevel.HIGH:
            score *= 0.6
        elif risk_level == RiskLevel.MEDIUM:
            score *= 0.8
        
        return max(0.0, min(1.0, score))
    
    def _generate_action_reasoning(
        self,
        action: str,
        success_impact: float,
        latency_impact: float,
        cost_impact: float,
        risk_level: RiskLevel
    ) -> str:
        """Generate reasoning for action score."""
        parts = [f"Action: {action}"]
        
        if success_impact > 0.1:
            parts.append(f"improves success rate by ~{success_impact*100:.0f}%")
        elif success_impact < -0.1:
            parts.append(f"may reduce success rate by ~{abs(success_impact)*100:.0f}%")
        
        if latency_impact > 0.1:
            parts.append(f"reduces latency")
        elif latency_impact < -0.1:
            parts.append(f"may increase latency")
        
        parts.append(f"risk: {risk_level.value}")
        
        return ", ".join(parts)
    
    def _select_best_action(
        self,
        scored_actions: List[ActionScore],
        reasoning: ReasoningResult
    ) -> Decision:
        """
        Select best action applying constraints.
        
        Args:
            scored_actions: List of scored actions
            reasoning: Original reasoning
            
        Returns:
            Final decision
        """
        # Sort by score
        sorted_actions = sorted(scored_actions, key=lambda x: x.score, reverse=True)
        
        # Track rejected actions
        rejected = {}
        active_constraints = []
        
        # Find first action that passes constraints
        selected = None
        for action in sorted_actions:
            # Check minimum confidence
            if action.score < self.constraints.min_confidence_for_action:
                rejected[action.action] = f"Score {action.score:.0%} below minimum {self.constraints.min_confidence_for_action:.0%}"
                continue
            
            # Check risk level
            if action.risk_level.value == RiskLevel.HIGH.value:
                if self.constraints.max_auto_approve_risk.value != RiskLevel.HIGH.value:
                    # Can still select but requires approval
                    pass
            
            # Check reversibility for high risk actions
            if action.risk_level in [RiskLevel.HIGH, RiskLevel.MEDIUM]:
                if action.reversibility < self.constraints.min_reversibility_for_high_risk:
                    rejected[action.action] = f"Reversibility {action.reversibility:.0%} too low for {action.risk_level.value} risk"
                    continue
            
            # This action passes constraints
            selected = action
            break
        
        # Fallback to do_nothing if no action passes
        if selected is None:
            selected = next(
                (a for a in sorted_actions if a.action == ActionType.DO_NOTHING.value),
                sorted_actions[0] if sorted_actions else ActionScore(
                    action=ActionType.DO_NOTHING.value,
                    score=0.5
                )
            )
            active_constraints.append("No action met all constraints, defaulting to do_nothing")
        
        # Determine if human approval required
        requires_approval = (
            selected.risk_level.value == RiskLevel.HIGH.value or
            (selected.risk_level.value == RiskLevel.MEDIUM.value and
             self.constraints.max_auto_approve_risk.value == RiskLevel.LOW.value)
        )
        
        # Generate reasoning summary
        top_hypothesis = reasoning.get_top_hypothesis()
        if top_hypothesis:
            reasoning_summary = f"{top_hypothesis[0]} detected with {top_hypothesis[1]:.0%} confidence"
        else:
            reasoning_summary = "No strong hypothesis detected"
        
        if selected.expected_success_rate_impact > 0.1:
            reasoning_summary += f", action expected to improve success rate"
        
        return Decision(
            selected_action=selected.action,
            confidence=selected.score,
            risk_level=selected.risk_level,
            requires_human_approval=requires_approval,
            reasoning_summary=reasoning_summary,
            considered_actions=sorted_actions,
            active_constraints=active_constraints,
            rejected_actions=rejected
        )

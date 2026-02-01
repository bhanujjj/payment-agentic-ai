"""
Outcome evaluator.

Evaluates whether an action succeeded, failed, or was neutral.
"""

import logging
from typing import Dict, Tuple

from agent.learning_models import OutcomeClassification


class OutcomeEvaluator:
    """
    Evaluates action outcomes based on metric changes.
    
    Uses deterministic rules to classify outcomes.
    """
    
    def __init__(self):
        """Initialize evaluator."""
        self.logger = logging.getLogger(__name__)
    
    def evaluate(
        self,
        pre_metrics: Dict[str, float],
        post_metrics: Dict[str, float],
        action: str
    ) -> Tuple[OutcomeClassification, float]:
        """
        Evaluate action outcome.
        
        Args:
            pre_metrics: Metrics before action
            post_metrics: Metrics after action
            action: Action that was taken
            
        Returns:
            (outcome_classification, outcome_score)
            
        Scoring:
            1.0 = perfect success
            0.5 = neutral (no change)
            0.0 = complete failure
        """
        # Compute deltas
        success_delta = post_metrics['success_rate'] - pre_metrics['success_rate']
        latency_delta = post_metrics['latency_ms'] - pre_metrics['latency_ms']
        retry_delta = post_metrics['retry_count'] - pre_metrics['retry_count']
        error_delta = post_metrics['error_rate'] - pre_metrics['error_rate']
        
        # Start with neutral baseline
        score = 0.5
        
        # Success rate impact (most important)
        if success_delta > 0.05:
            score += 0.3  # significant improvement
            self.logger.debug(f"Success rate improved by {success_delta:.1%}")
        elif success_delta > 0.02:
            score += 0.15  # moderate improvement
        elif success_delta < -0.05:
            score -= 0.3  # significant degradation
            self.logger.debug(f"Success rate degraded by {success_delta:.1%}")
        elif success_delta < -0.02:
            score -= 0.15  # moderate degradation
        
        # Latency impact
        if latency_delta < -100:
            score += 0.15  # latency improved
            self.logger.debug(f"Latency improved by {-latency_delta:.0f}ms")
        elif latency_delta > 100:
            score -= 0.15  # latency degraded
            self.logger.debug(f"Latency degraded by {latency_delta:.0f}ms")
        
        # Retry impact
        if retry_delta < -10:
            score += 0.1  # retries reduced
            self.logger.debug(f"Retries reduced by {-retry_delta}")
        elif retry_delta > 10:
            score -= 0.1  # retries increased
            self.logger.debug(f"Retries increased by {retry_delta}")
        
        # Error rate impact
        if error_delta < -0.03:
            score += 0.1  # errors reduced
        elif error_delta > 0.03:
            score -= 0.1  # errors increased
        
        # Clamp score to [0, 1]
        score = max(0.0, min(1.0, score))
        
        # Classify based on score
        if score >= 0.7:
            classification = OutcomeClassification.SUCCESS
        elif score <= 0.3:
            classification = OutcomeClassification.FAILURE
        else:
            classification = OutcomeClassification.NEUTRAL
        
        self.logger.info(
            f"Outcome evaluation: {classification.value} (score: {score:.2f})"
        )
        
        return classification, score
    
    def evaluate_from_signals(
        self,
        pre_signals,
        post_signals,
        action: str
    ) -> Tuple[OutcomeClassification, float]:
        """
        Evaluate from PaymentSignals objects.
        
        IMPORTANT: Handles causality correctly for non-intervention actions.
        
        Args:
            pre_signals: PaymentSignals before action
            post_signals: PaymentSignals after action
            action: Action that was taken
            
        Returns:
            (outcome_classification, outcome_score)
        """
        # CAUSALITY CHECK: Non-intervention actions cannot claim credit
        # do_nothing and alert_ops do not modify system state
        # Any metric changes are due to natural variance, not agent action
        if action in ['do_nothing', 'alert_ops']:
            self.logger.info(
                f"Outcome evaluation: NEUTRAL (non-intervention action: {action})"
            )
            self.logger.info(
                "Reason: No intervention applied; metric changes not attributed to agent"
            )
            return OutcomeClassification.NEUTRAL, 0.5
        
        # For intervention actions, proceed with normal evaluation
        pre_metrics = {
            'success_rate': pre_signals.overall_success_rate,
            'latency_ms': pre_signals.avg_latency_ms,
            'retry_count': pre_signals.total_retries,
            'error_rate': pre_signals.overall_failure_rate
        }
        
        post_metrics = {
            'success_rate': post_signals.overall_success_rate,
            'latency_ms': post_signals.avg_latency_ms,
            'retry_count': post_signals.total_retries,
            'error_rate': post_signals.overall_failure_rate
        }
        
        return self.evaluate(pre_metrics, post_metrics, action)

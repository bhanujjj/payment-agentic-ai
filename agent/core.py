"""
Core agent implementation.

The PaymentAgent is the main autonomous entity that:
1. Observes payment events and computes signals.
2. Evaluates and learns from past action outcomes.
3. Reasons about failures and uncertainties using AI.
4. Decides on actions using context-aware scoring and constraints.
5. Executes actions safely.
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

from simulation.models import PaymentRecord
from agent.metrics import MetricsEngine
from agent.reasoner import Reasoner
from agent.decider import DecisionEngine
from agent.executor import ActionExecutor
from agent.evaluator import OutcomeEvaluator
from agent.memory import ActionMemory
from agent.learner import ActionLearner
from agent.signals import PaymentSignals
from agent.decision_models import Decision


class PaymentAgent:
    """
    Main autonomous agent for payment operations.
    
    This agent operates in a continuous loop:
    - Observe → Reason → Decide → Act → Learn
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None, environment: Any = None):
        """
        Initialize the payment agent and all its subcomponents.
        
        Args:
            config: Configuration dictionary
            environment: Optional simulation environment (for backwards compatibility)
        """
        self.config = config or {}
        self.environment = environment
        self.logger = logging.getLogger(__name__)
        
        # Load sub-configs
        agent_config = self.config.get("agent", {})
        llm_config = self.config.get("llm", {})
        memory_config = self.config.get("memory", {})
        decision_config = self.config.get("decision", {})
        
        # Set up memory and learning
        memory_path = memory_config.get("path", "./data/memory/agent_memory.json")
        self.memory = ActionMemory(storage_path=memory_path)
        self.learner = ActionLearner(self.memory)
        
        # Initialize agent components
        self.metrics_engine = MetricsEngine(config=self.config.get("metrics"))
        self.reasoner = Reasoner(config=llm_config)
        self.decider = DecisionEngine(config=decision_config, learner=self.learner)
        self.executor = ActionExecutor()
        self.evaluator = OutcomeEvaluator()
        
        # Internal state tracking for sequential runs
        self.last_signals: Optional[PaymentSignals] = None
        self.last_decision: Optional[Decision] = None
        self.last_action: Optional[str] = None
        
        self.logger.info("PaymentAgent initialized successfully")
        
    async def run_step(
        self,
        payments: List[PaymentRecord],
        prev_signals: Optional[PaymentSignals] = None,
        prev_decision: Optional[Decision] = None,
        prev_action: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Perform a single iteration of the observe-reason-decide-act-learn cycle.
        
        Args:
            payments: List of payment records in the current window.
            prev_signals: Signals from the previous window (defaults to self.last_signals).
            prev_decision: Decision from the previous window (defaults to self.last_decision).
            prev_action: Action name from the previous window (fallback if prev_decision not provided).
            
        Returns:
            Dictionary summarizing the observations, reasoning, decision, execution, and learning.
        """
        self.logger.info(f"Processing step with {len(payments)} payments")
        
        # 1. Observe (Compute signals)
        current_signals = self.metrics_engine.compute_signals(payments)
        
        # Resolve prev_decision from string fallback if needed
        if prev_decision is None:
            active_action = prev_action or self.last_action
            if active_action:
                from agent.decision_models import Decision, RiskLevel
                prev_decision = Decision(
                    selected_action=active_action,
                    confidence=1.0,
                    risk_level=RiskLevel.MEDIUM,
                    requires_human_approval=False,
                    reasoning_summary="",
                    considered_actions=[]
                )
            else:
                prev_decision = self.last_decision
                
        active_prev_signals = prev_signals or self.last_signals
        active_prev_decision = prev_decision
        
        # 2. Learn (Evaluate previous action outcome and record it in memory)
        learning_result = None
        if (active_prev_signals and active_prev_decision and 
                active_prev_decision.selected_action != "do_nothing" and 
                active_prev_decision.selected_action != "alert_ops"):
            try:
                outcome_class, outcome_score = self.evaluator.evaluate_from_signals(
                    pre_signals=active_prev_signals,
                    post_signals=current_signals,
                    action=active_prev_decision.selected_action
                )
                
                # Construct ActionOutcome
                from agent.learning_models import ActionOutcome
                
                outcome = ActionOutcome(
                    context_summary=self.decider._summarize_context(active_prev_signals),
                    action=active_prev_decision.selected_action,
                    risk_level=active_prev_decision.risk_level.value,
                    pre_success_rate=active_prev_signals.overall_success_rate,
                    pre_latency_ms=active_prev_signals.avg_latency_ms,
                    pre_retry_count=active_prev_signals.total_retries,
                    pre_error_rate=active_prev_signals.overall_failure_rate,
                    post_success_rate=current_signals.overall_success_rate,
                    post_latency_ms=current_signals.avg_latency_ms,
                    post_retry_count=current_signals.total_retries,
                    post_error_rate=current_signals.overall_failure_rate,
                    success_rate_delta=current_signals.overall_success_rate - active_prev_signals.overall_success_rate,
                    latency_delta=current_signals.avg_latency_ms - active_prev_signals.avg_latency_ms,
                    retry_delta=current_signals.total_retries - active_prev_signals.total_retries,
                    error_rate_delta=current_signals.overall_failure_rate - active_prev_signals.overall_failure_rate,
                    outcome=outcome_class,
                    outcome_score=outcome_score,
                    timestamp=datetime.utcnow(),
                    notes="Iterative agent run step"
                )
                
                # Save outcome to memory
                self.memory.add(outcome)
                self.memory.save()
                
                learning_result = {
                    "action": active_prev_decision.selected_action,
                    "outcome": outcome.to_dict(),
                    "success": outcome_class.value == "SUCCESS"
                }
                self.logger.info(f"Recorded learning outcome for {active_prev_decision.selected_action}: {outcome_score}")
            except Exception as e:
                self.logger.error(f"Error during learning evaluation: {e}", exc_info=True)
                learning_result = {"error": str(e)}
        
        # 3. Reason
        try:
            reasoning = await self.reasoner.reason(current_signals)
        except Exception as e:
            self.logger.error(f"Error during reasoning: {e}", exc_info=True)
            # Safe empty reasoning fallback
            from agent.reasoning_models import ReasoningResult
            reasoning = ReasoningResult(
                hypotheses={"normal_operation": 0.5},
                explanation=f"Reasoning failed: {e}",
                assumptions=[],
                uncertainty=["Reasoning error"],
                overall_confidence=0.5
            )
            
        # 4. Decide
        try:
            decision = self.decider.decide(reasoning, current_signals)
        except Exception as e:
            self.logger.error(f"Error during decision: {e}", exc_info=True)
            from agent.decision_models import Decision, RiskLevel
            decision = Decision(
                selected_action="do_nothing",
                confidence=0.5,
                risk_level=RiskLevel.LOW,
                requires_human_approval=False,
                reasoning_summary=f"Decision failed, defaulting to do_nothing: {e}",
                considered_actions=[]
            )
            
        # 5. Act (Execute action)
        try:
            execution_result = self.executor.execute(decision, current_signals)
        except Exception as e:
            self.logger.error(f"Error during execution: {e}", exc_info=True)
            from agent.execution_models import ExecutionResult, ExecutionStatus
            execution_result = ExecutionResult(
                action=decision.selected_action,
                executed=False,
                status=ExecutionStatus.FAILED,
                impact_scope="system",
                expected_effect="",
                timestamp=datetime.utcnow(),
                error=str(e)
            )
            
        # Store state for next window
        self.last_signals = current_signals
        self.last_decision = decision
        self.last_action = decision.selected_action
        
        return {
            "signals": current_signals,
            "reasoning": reasoning,
            "decision": decision,
            "execution": execution_result,
            "learning": learning_result
        }
        
    async def run(self):
        """
        Backwards-compatible main loop logging.
        """
        self.logger.info("Agent started - use run_step for iterative real data processing")
        
    async def shutdown(self):
        """
        Graceful shutdown.
        """
        self.logger.info("Agent shutting down")

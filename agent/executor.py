"""
Action executor.

Executes or blocks actions based on decision engine output.
This is a SIMULATED executor - no real system changes.
"""

import logging
from datetime import datetime
from typing import Optional

from agent.decision_models import Decision
from agent.execution_models import ExecutionResult, ExecutionStatus, SystemState
from agent.signals import PaymentSignals


class ActionExecutor:
    """
    Executes actions from the decision engine.
    
    Key responsibilities:
    1. Enforce approval guardrails
    2. Execute safe, simulated actions
    3. Update system state
    4. Return structured results
    
    IMPORTANT: This executor is SIMULATED ONLY.
    No real APIs, no real system changes.
    """
    
    def __init__(self, system_state: Optional[SystemState] = None):
        """
        Initialize executor.
        
        Args:
            system_state: System state to manage (creates new if None)
        """
        self.logger = logging.getLogger(__name__)
        self.system_state = system_state or SystemState()
        
    def execute(
        self,
        decision: Decision,
        signals: PaymentSignals
    ) -> ExecutionResult:
        """
        Execute or block an action based on decision.
        
        Args:
            decision: Decision from decision engine
            signals: Current payment signals (for context)
            
        Returns:
            Execution result
        """
        self.logger.info(f"Executing action: {decision.selected_action}")
        
        # GUARDRAIL: Check approval requirement
        if decision.requires_human_approval:
            return self._block_for_approval(decision, signals)
        
        # Execute action based on type
        action = decision.selected_action
        
        try:
            if action == "do_nothing":
                return self._execute_do_nothing(decision, signals)
            elif action == "alert_ops":
                return self._execute_alert_ops(decision, signals)
            elif action == "recommend_reroute":
                return self._execute_recommend_reroute(decision, signals)
            elif action == "recommend_path_suppression":
                return self._execute_recommend_path_suppression(decision, signals)
            elif action == "recommend_circuit_breaker":
                return self._execute_recommend_circuit_breaker(decision, signals)
            elif action == "recommend_retry_adjustment":
                return self._execute_recommend_retry_adjustment(decision, signals)
            else:
                return self._execute_unknown_action(decision, signals)
                
        except Exception as e:
            self.logger.error(f"Execution failed: {e}", exc_info=True)
            return ExecutionResult(
                action=action,
                executed=False,
                status=ExecutionStatus.FAILED,
                impact_scope="system",
                expected_effect="",
                timestamp=datetime.utcnow(),
                error=str(e)
            )
    
    def _block_for_approval(
        self,
        decision: Decision,
        signals: PaymentSignals
    ) -> ExecutionResult:
        """Block action pending human approval."""
        self.logger.warning(
            f"Action {decision.selected_action} requires human approval. Blocking."
        )
        
        # Determine impact scope
        impact_scope = self._determine_impact_scope(decision, signals)
        
        return ExecutionResult(
            action=decision.selected_action,
            executed=False,
            status=ExecutionStatus.PENDING_HUMAN_APPROVAL,
            impact_scope=impact_scope,
            expected_effect=decision.reasoning_summary,
            timestamp=datetime.utcnow(),
            reasoning=f"Risk level {decision.risk_level.value} requires approval"
        )
    
    def _execute_do_nothing(
        self,
        decision: Decision,
        signals: PaymentSignals
    ) -> ExecutionResult:
        """Execute do_nothing action (just observe)."""
        self.logger.info("Action: do_nothing - monitoring only")
        
        self.system_state.last_action = "do_nothing"
        self.system_state.last_updated = datetime.utcnow()
        
        return ExecutionResult(
            action="do_nothing",
            executed=True,
            status=ExecutionStatus.EXECUTED,
            impact_scope="none",
            expected_effect="Continue monitoring system health",
            timestamp=datetime.utcnow(),
            state_changes={},
            reasoning="System is operating within acceptable parameters"
        )
    
    def _execute_alert_ops(
        self,
        decision: Decision,
        signals: PaymentSignals
    ) -> ExecutionResult:
        """Execute alert_ops action."""
        self.logger.info("Action: alert_ops - sending notification")
        
        # Create alert message
        alert_msg = f"Payment system alert: {decision.reasoning_summary}"
        if signals.degraded_banks:
            alert_msg += f" | Degraded banks: {', '.join(signals.degraded_banks)}"
        
        # Add to system state
        self.system_state.alerts.append(alert_msg)
        self.system_state.last_action = "alert_ops"
        self.system_state.last_updated = datetime.utcnow()
        
        return ExecutionResult(
            action="alert_ops",
            executed=True,
            status=ExecutionStatus.EXECUTED,
            impact_scope="operations_team",
            expected_effect="Operations team notified of system degradation",
            timestamp=datetime.utcnow(),
            state_changes={"alerts": [alert_msg]},
            reasoning="Alert sent to operations team for awareness"
        )
    
    def _execute_recommend_reroute(
        self,
        decision: Decision,
        signals: PaymentSignals
    ) -> ExecutionResult:
        """Execute recommend_reroute action."""
        self.logger.info("Action: recommend_reroute - updating routing state")
        
        # Identify banks to reroute from
        affected_banks = signals.degraded_banks or []
        
        # Update dynamic routing config state
        from simulation.routing_config import ROUTING_STATE
        for bank in affected_banks:
            self.system_state.routing_overrides[bank] = "rerouted"
            if bank in ROUTING_STATE["active_banks"]:
                ROUTING_STATE["active_banks"].remove(bank)
        
        self.system_state.last_action = "recommend_reroute"
        self.system_state.last_updated = datetime.utcnow()
        
        impact_scope = ", ".join(affected_banks) if affected_banks else "all_banks"
        
        return ExecutionResult(
            action="recommend_reroute",
            executed=True,
            status=ExecutionStatus.EXECUTED,
            impact_scope=impact_scope,
            expected_effect=f"Traffic rerouted away from degraded banks: {impact_scope}",
            timestamp=datetime.utcnow(),
            state_changes={"routing_overrides": dict(self.system_state.routing_overrides)},
            reasoning="Rerouting traffic to improve success rate"
        )
    
    def _execute_recommend_path_suppression(
        self,
        decision: Decision,
        signals: PaymentSignals
    ) -> ExecutionResult:
        """Execute recommend_path_suppression action."""
        self.logger.info("Action: recommend_path_suppression - suppressing paths in state")
        
        # Identify banks to suppress
        affected_banks = signals.degraded_banks or []
        
        # Update dynamic routing config state
        from simulation.routing_config import ROUTING_STATE
        for bank in affected_banks:
            self.system_state.routing_overrides[bank] = "suppressed"
            if bank not in ROUTING_STATE["suppressed_banks"]:
                ROUTING_STATE["suppressed_banks"].append(bank)
        
        self.system_state.last_action = "recommend_path_suppression"
        self.system_state.last_updated = datetime.utcnow()
        
        impact_scope = ", ".join(affected_banks) if affected_banks else "degraded_paths"
        
        return ExecutionResult(
            action="recommend_path_suppression",
            executed=True,
            status=ExecutionStatus.EXECUTED,
            impact_scope=impact_scope,
            expected_effect=f"Suppressed payment paths for: {impact_scope}",
            timestamp=datetime.utcnow(),
            state_changes={"routing_overrides": dict(self.system_state.routing_overrides)},
            reasoning="Suppressing degraded paths to prevent failures"
        )
    
    def _execute_recommend_circuit_breaker(
        self,
        decision: Decision,
        signals: PaymentSignals
    ) -> ExecutionResult:
        """Execute recommend_circuit_breaker action."""
        self.logger.info("Action: recommend_circuit_breaker - enabling breakers in state")
        
        # Enable circuit breakers for degraded banks
        affected_banks = signals.degraded_banks or []
        
        from simulation.routing_config import ROUTING_STATE
        for bank in affected_banks:
            self.system_state.circuit_breakers[bank] = True
            if bank not in ROUTING_STATE["suppressed_banks"]:
                ROUTING_STATE["suppressed_banks"].append(bank)  # Suppress traffic
        
        self.system_state.last_action = "recommend_circuit_breaker"
        self.system_state.last_updated = datetime.utcnow()
        
        impact_scope = ", ".join(affected_banks) if affected_banks else "degraded_banks"
        
        return ExecutionResult(
            action="recommend_circuit_breaker",
            executed=True,
            status=ExecutionStatus.EXECUTED,
            impact_scope=impact_scope,
            expected_effect=f"Circuit breakers enabled for: {impact_scope}",
            timestamp=datetime.utcnow(),
            state_changes={"circuit_breakers": dict(self.system_state.circuit_breakers)},
            reasoning="Circuit breakers prevent cascading failures"
        )
    
    def _execute_recommend_retry_adjustment(
        self,
        decision: Decision,
        signals: PaymentSignals
    ) -> ExecutionResult:
        """Execute recommend_retry_adjustment action."""
        self.logger.info("Action: recommend_retry_adjustment - adjusting retries in state")
        
        from simulation.routing_config import ROUTING_STATE
        # Reduce retries if retry storm detected
        if signals.total_retries > signals.total_payments * 0.3:
            # High retry rate - reduce to 1 retry max
            self.system_state.retry_policy["max_retries"] = 1
            for method in ["UPI", "CARD", "NETBANKING", "WALLET"]:
                ROUTING_STATE["retry_limits"][method] = 1
            effect = "Reduced max retries to 1 to prevent retry storm"
        else:
            # Normal - keep moderate (2 retries max)
            self.system_state.retry_policy["max_retries"] = 2
            for method in ["UPI", "CARD", "NETBANKING", "WALLET"]:
                ROUTING_STATE["retry_limits"][method] = 2
            effect = "Set max retries to 2 for balanced reliability"
        
        self.system_state.last_action = "recommend_retry_adjustment"
        self.system_state.last_updated = datetime.utcnow()
        
        return ExecutionResult(
            action="recommend_retry_adjustment",
            executed=True,
            status=ExecutionStatus.EXECUTED,
            impact_scope="retry_policy",
            expected_effect=effect,
            timestamp=datetime.utcnow(),
            state_changes={"retry_policy": dict(self.system_state.retry_policy)},
            reasoning="Adjusted retry policy based on current retry effectiveness"
        )
    
    def _execute_unknown_action(
        self,
        decision: Decision,
        signals: PaymentSignals
    ) -> ExecutionResult:
        """Handle unknown action."""
        self.logger.warning(f"Unknown action: {decision.selected_action}")
        
        return ExecutionResult(
            action=decision.selected_action,
            executed=False,
            status=ExecutionStatus.BLOCKED,
            impact_scope="none",
            expected_effect="",
            timestamp=datetime.utcnow(),
            error=f"Unknown action type: {decision.selected_action}"
        )
    
    def _determine_impact_scope(
        self,
        decision: Decision,
        signals: PaymentSignals
    ) -> str:
        """Determine the scope of impact for an action."""
        if signals.degraded_banks:
            return ", ".join(signals.degraded_banks)
        elif signals.degraded_methods:
            return ", ".join(signals.degraded_methods)
        else:
            return "system"
    
    def get_state(self) -> SystemState:
        """Get current system state."""
        return self.system_state
    
    def reset_state(self):
        """Reset system state to defaults."""
        self.logger.info("Resetting system state")
        self.system_state.reset()

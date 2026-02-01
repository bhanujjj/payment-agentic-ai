"""
Action Execution Examples

Demonstrates the full pipeline: Signals → Reasoning → Decision → Execution
"""

import asyncio
import logging
from simulation.generator import PaymentGenerator
from agent.metrics import MetricsEngine
from agent.reasoner import Reasoner
from agent.decider import DecisionEngine
from agent.executor import ActionExecutor

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def main():
    """Run action execution examples."""
    
    logger.info("=" * 70)
    logger.info("ACTION EXECUTION EXAMPLES")
    logger.info("=" * 70)
    
    # Initialize components
    executor = ActionExecutor()
    reasoner = Reasoner()
    decider = DecisionEngine()
    engine = MetricsEngine()
    
    # Example 1: Normal Operation (do_nothing)
    logger.info("\n=== Example 1: Normal Operation ===\n")
    gen1 = PaymentGenerator(config={'seed': 42})
    payments1 = gen1.generate_batch(count=200, time_span_seconds=300)
    signals1 = engine.compute_signals(payments1)
    reasoning1 = await reasoner.reason(signals1)
    decision1 = decider.decide(reasoning1, signals1)
    result1 = executor.execute(decision1, signals1)
    
    logger.info(f"Scenario: Normal operation ({signals1.overall_success_rate:.1%} success)")
    logger.info(f"Decision: {decision1.selected_action}")
    logger.info(f"Execution Status: {result1.status.value}")
    logger.info(f"Executed: {result1.executed}")
    logger.info(f"Impact: {result1.impact_scope}")
    logger.info(f"Effect: {result1.expected_effect}")
    
    # Example 2: Bank Degradation (alert_ops)
    logger.info("\n=== Example 2: Bank Degradation ===\n")
    executor.reset_state()  # Reset state
    gen2 = PaymentGenerator(config={'seed': 42})
    gen2.simulate_bank_degradation('HDFC Bank')
    payments2 = gen2.generate_batch(count=200, time_span_seconds=300)
    signals2 = engine.compute_signals(payments2)
    reasoning2 = await reasoner.reason(signals2)
    decision2 = decider.decide(reasoning2, signals2)
    result2 = executor.execute(decision2, signals2)
    
    logger.info(f"Scenario: HDFC degraded ({signals2.overall_success_rate:.1%} success)")
    logger.info(f"Decision: {decision2.selected_action}")
    logger.info(f"Execution Status: {result2.status.value}")
    logger.info(f"Executed: {result2.executed}")
    logger.info(f"State Changes: {result2.state_changes}")
    
    # Example 3: Critical Scenario (requires approval)
    logger.info("\n=== Example 3: Critical Scenario (Approval Required) ===\n")
    executor.reset_state()
    gen3 = PaymentGenerator(config={'seed': 42})
    gen3.simulate_bank_outage('HDFC Bank')
    gen3.simulate_bank_outage('ICICI Bank')
    payments3 = gen3.generate_batch(count=200, time_span_seconds=300)
    signals3 = engine.compute_signals(payments3)
    reasoning3 = await reasoner.reason(signals3)
    decision3 = decider.decide(reasoning3, signals3)
    result3 = executor.execute(decision3, signals3)
    
    logger.info(f"Scenario: Both banks down ({signals3.overall_success_rate:.1%} success)")
    logger.info(f"Decision: {decision3.selected_action}")
    logger.info(f"Requires Approval: {decision3.requires_human_approval}")
    logger.info(f"Execution Status: {result3.status.value}")
    logger.info(f"Executed: {result3.executed}")
    logger.info(f"Reasoning: {result3.reasoning}")
    
    if result3.status.value == "PENDING_HUMAN_APPROVAL":
        logger.info("⚠️  Action blocked - waiting for human approval")
        logger.info(f"   Impact Scope: {result3.impact_scope}")
        logger.info(f"   Expected Effect: {result3.expected_effect}")
    
    # Example 4: System State Inspection
    logger.info("\n=== Example 4: System State After Execution ===\n")
    executor.reset_state()
    
    # Execute a path suppression
    gen4 = PaymentGenerator(config={'seed': 42})
    gen4.simulate_bank_degradation('HDFC Bank')
    gen4.simulate_bank_degradation('Axis Bank')
    payments4 = gen4.generate_batch(count=200, time_span_seconds=300)
    signals4 = engine.compute_signals(payments4)
    reasoning4 = await reasoner.reason(signals4)
    decision4 = decider.decide(reasoning4, signals4)
    
    # Force execution (bypass approval for demo)
    decision4.requires_human_approval = False
    result4 = executor.execute(decision4, signals4)
    
    logger.info(f"Action: {result4.action}")
    logger.info(f"Executed: {result4.executed}")
    logger.info("\nSystem State:")
    state = executor.get_state()
    logger.info(f"  Routing Overrides: {state.routing_overrides}")
    logger.info(f"  Circuit Breakers: {state.circuit_breakers}")
    logger.info(f"  Retry Policy: {state.retry_policy}")
    logger.info(f"  Active Alerts: {len(state.alerts)}")
    logger.info(f"  Last Action: {state.last_action}")
    
    # Example 5: JSON Export
    logger.info("\n=== Example 5: Execution Result as JSON ===\n")
    result_dict = result4.to_dict()
    import json
    logger.info(json.dumps(result_dict, indent=2, default=str))
    
    logger.info("\n" + "=" * 70)
    logger.info("=== All examples completed ===")
    logger.info("=" * 70)


if __name__ == "__main__":
    asyncio.run(main())

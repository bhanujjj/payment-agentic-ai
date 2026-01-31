"""
Example usage of the decision engine.

Demonstrates how to use the decision engine to make decisions based on reasoning.
"""

import asyncio
import logging
import json
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

from simulation.generator import PaymentGenerator
from agent.metrics import MetricsEngine
from agent.reasoner import Reasoner
from agent.decider import DecisionEngine
from agent.decision_models import DecisionConstraints, RiskLevel

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def main():
    """Run decision engine examples."""
    
    logger.info("Decision Engine Examples")
    logger.info("=" * 60)
    
    # Initialize components
    gen = PaymentGenerator(config={'seed': 42})
    metrics_engine = MetricsEngine()
    reasoner = Reasoner()
    decision_engine = DecisionEngine()
    
    # Example 1: Normal Operation
    logger.info("\n=== Example 1: Normal Operation ===\n")
    
    gen.base_failure_rate = 0.02
    payments = gen.generate_batch(count=100, time_span_seconds=300)
    
    signals = metrics_engine.compute_signals(payments)
    reasoning = await reasoner.reason(signals)
    decision = decision_engine.decide(reasoning, signals)
    
    logger.info(f"Signals: {signals.overall_success_rate:.1%} success rate")
    logger.info(f"Reasoning: {reasoning.get_top_hypothesis()}")
    logger.info(f"\nDecision:")
    logger.info(decision.get_summary())
    
    # Example 2: Bank Degradation
    logger.info("\n=== Example 2: Bank Degradation ===\n")
    
    gen = PaymentGenerator(config={'seed': 42})
    gen.simulate_bank_degradation("HDFC Bank")
    payments = gen.generate_batch(count=200, time_span_seconds=300)
    
    signals = metrics_engine.compute_signals(payments)
    reasoning = await reasoner.reason(signals)
    decision = decision_engine.decide(reasoning, signals)
    
    logger.info(f"Signals: {signals.overall_success_rate:.1%} success rate")
    logger.info(f"Degraded Banks: {signals.degraded_banks}")
    logger.info(f"Reasoning: {reasoning.get_top_hypothesis()}")
    logger.info(f"\nDecision:")
    logger.info(decision.get_summary())
    
    logger.info(f"\nAll Considered Actions:")
    for action in decision.considered_actions[:5]:
        logger.info(f"  • {action.action}: {action.score:.0%} (risk: {action.risk_level.value})")
    
    # Example 3: Multiple Issues
    logger.info("\n=== Example 3: Multiple Issues ===\n")
    
    gen = PaymentGenerator(config={'seed': 42})
    gen.simulate_bank_outage("ICICI Bank")
    gen.simulate_bank_degradation("HDFC Bank")
    payments = gen.generate_batch(count=200, time_span_seconds=300)
    
    signals = metrics_engine.compute_signals(payments)
    reasoning = await reasoner.reason(signals)
    decision = decision_engine.decide(reasoning, signals)
    
    logger.info(f"Signals: {signals.overall_success_rate:.1%} success rate")
    logger.info(f"Degraded Banks: {signals.degraded_banks}")
    logger.info(f"\nDecision:")
    logger.info(decision.get_summary())
    
    # Example 4: Strict Constraints
    logger.info("\n=== Example 4: Strict Constraints ===\n")
    
    constraints = DecisionConstraints(
        max_auto_approve_risk=RiskLevel.LOW,
        min_confidence_for_action=0.7,
        allow_rerouting=False
    )
    strict_engine = DecisionEngine(constraints=constraints)
    
    gen = PaymentGenerator(config={'seed': 42})
    gen.simulate_bank_degradation("SBI")
    payments = gen.generate_batch(count=150, time_span_seconds=300)
    
    signals = metrics_engine.compute_signals(payments)
    reasoning = await reasoner.reason(signals)
    decision = strict_engine.decide(reasoning, signals)
    
    logger.info(f"Constraints: max_risk={constraints.max_auto_approve_risk.value}, allow_rerouting={constraints.allow_rerouting}")
    logger.info(f"\nDecision:")
    logger.info(decision.get_summary())
    
    if decision.rejected_actions:
        logger.info(f"\nRejected Actions:")
        for action, reason in decision.rejected_actions.items():
            logger.info(f"  • {action}: {reason}")
    
    # Example 5: JSON Export
    logger.info("\n=== Example 5: JSON Export ===\n")
    
    gen = PaymentGenerator(config={'seed': 42})
    gen.simulate_bank_degradation("Axis Bank")
    payments = gen.generate_batch(count=100, time_span_seconds=300)
    
    signals = metrics_engine.compute_signals(payments)
    reasoning = await reasoner.reason(signals)
    decision = decision_engine.decide(reasoning, signals)
    
    logger.info("Decision as JSON:")
    logger.info(json.dumps(decision.to_dict(), indent=2)[:500] + "...")
    
    # Example 6: High Risk Action
    logger.info("\n=== Example 6: High Risk Scenario ===\n")
    
    gen = PaymentGenerator(config={'seed': 42})
    gen.simulate_bank_outage("HDFC Bank")
    gen.simulate_bank_outage("ICICI Bank")
    payments = gen.generate_batch(count=200, time_span_seconds=300)
    
    signals = metrics_engine.compute_signals(payments)
    reasoning = await reasoner.reason(signals)
    decision = decision_engine.decide(reasoning, signals)
    
    logger.info(f"Signals: {signals.overall_success_rate:.1%} success rate")
    logger.info(f"Degraded Banks: {signals.degraded_banks}")
    logger.info(f"\nDecision:")
    logger.info(decision.get_summary())
    
    if decision.requires_human_approval:
        logger.info(f"\n⚠️  This decision requires human approval!")
        logger.info(f"   Risk Level: {decision.risk_level.value}")
    
    logger.info("\n" + "=" * 60)
    logger.info("=== All examples completed ===")


if __name__ == "__main__":
    asyncio.run(main())

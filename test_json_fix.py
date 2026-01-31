"""
Quick test for JSON parsing fix.
"""

import asyncio
import logging
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
    """Test JSON parsing with Gemini."""
    
    logger.info("Testing Gemini JSON Mode")
    logger.info("=" * 60)
    
    # Generate test data
    gen = PaymentGenerator(config={'seed': 42})
    gen.simulate_bank_degradation("HDFC Bank")
    payments = gen.generate_batch(count=200, time_span_seconds=300)
    
    # Compute signals
    metrics_engine = MetricsEngine()
    signals = metrics_engine.compute_signals(payments)
    
    logger.info(f"Signals: {signals.overall_success_rate:.1%} success rate")
    logger.info(f"Degraded Banks: {signals.degraded_banks}")
    
    # Test reasoning
    reasoner = Reasoner()
    reasoning = await reasoner.reason(signals)
    
    logger.info(f"\nReasoning Result:")
    logger.info(f"  Top Hypothesis: {reasoning.get_top_hypothesis()}")
    logger.info(f"  Confidence: {reasoning.overall_confidence:.0%}")
    logger.info(f"  Explanation: {reasoning.explanation}")
    
    # Test decision
    constraints = DecisionConstraints(max_auto_approve_risk=RiskLevel.MEDIUM)
    decider = DecisionEngine(constraints=constraints)
    decision = decider.decide(reasoning, signals)
    
    logger.info(f"\nDecision:")
    logger.info(decision.get_summary())
    
    logger.info("\n" + "=" * 60)
    logger.info("✅ Test completed successfully!")
    logger.info("If you saw 'Failed to parse LLM response' errors, the fix didn't work.")
    logger.info("If you saw no parsing errors, the fix worked!")


if __name__ == "__main__":
    asyncio.run(main())

"""
Example usage of the reasoning layer.

Demonstrates how to use the LLM-based reasoner to interpret payment signals.
"""

import asyncio
import logging
import json
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

from simulation.generator import PaymentGenerator
from agent.metrics import MetricsEngine
from agent.reasoner import Reasoner


# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def example_basic_reasoning():
    """Example: Basic reasoning from signals."""
    logger.info("=== Example 1: Basic Reasoning ===\n")
    
    # Generate payment data
    generator = PaymentGenerator(config={"seed": 42})
    payments = generator.generate_batch(count=100, time_span_seconds=300)
    
    # Compute signals
    metrics_engine = MetricsEngine()
    signals = metrics_engine.compute_signals(payments)
    
    # Reason about signals
    reasoner = Reasoner()
    reasoning = await reasoner.reason(signals)
    
    # Display results
    logger.info(reasoning.get_summary())
    logger.info(f"\nAssumptions: {reasoning.assumptions}")
    logger.info(f"Uncertainty: {reasoning.uncertainty}")


async def example_bank_degradation_reasoning():
    """Example: Reasoning about bank degradation."""
    logger.info("\n=== Example 2: Bank Degradation Reasoning ===\n")
    
    generator = PaymentGenerator(config={"seed": 42})
    
    # Simulate HDFC Bank degradation
    generator.simulate_bank_degradation("HDFC Bank")
    payments = generator.generate_batch(count=200, time_span_seconds=300)
    
    # Compute signals
    metrics_engine = MetricsEngine()
    signals = metrics_engine.compute_signals(payments)
    
    logger.info(f"Input Signals: {signals.get_summary()}\n")
    
    # Reason about it
    reasoner = Reasoner()
    reasoning = await reasoner.reason(signals)
    
    logger.info(reasoning.get_summary())
    
    # Check if it detected bank degradation
    if "bank_degradation" in reasoning.hypotheses:
        logger.info(f"\n✅ Correctly identified bank degradation!")
        logger.info(f"   Confidence: {reasoning.hypotheses['bank_degradation']:.0%}")


async def example_multiple_issues_reasoning():
    """Example: Reasoning about multiple simultaneous issues."""
    logger.info("\n=== Example 3: Multiple Issues Reasoning ===\n")
    
    generator = PaymentGenerator(config={"seed": 42})
    
    # Create complex scenario
    generator.simulate_bank_outage("ICICI Bank")
    generator.simulate_bank_degradation("HDFC Bank")
    generator.base_latency_ms = 800  # High latency
    
    payments = generator.generate_batch(count=250, time_span_seconds=300)
    
    # Compute signals
    metrics_engine = MetricsEngine()
    signals = metrics_engine.compute_signals(payments)
    
    logger.info(f"Input Signals:")
    logger.info(f"  Degraded Banks: {signals.degraded_banks}")
    logger.info(f"  Success Rate: {signals.overall_success_rate:.1%}")
    logger.info(f"  P95 Latency: {signals.p95_latency_ms:.0f}ms\n")
    
    # Reason about it
    reasoner = Reasoner()
    reasoning = await reasoner.reason(signals)
    
    logger.info(reasoning.get_summary())
    logger.info(f"\nAll Hypotheses:")
    for hyp, conf in sorted(reasoning.hypotheses.items(), key=lambda x: x[1], reverse=True):
        logger.info(f"  • {hyp}: {conf:.0%}")


async def example_normal_operation_reasoning():
    """Example: Reasoning about normal operation."""
    logger.info("\n=== Example 4: Normal Operation Reasoning ===\n")
    
    generator = PaymentGenerator(config={"seed": 42})
    
    # Normal operation with low failure rate
    generator.base_failure_rate = 0.02
    payments = generator.generate_batch(count=150, time_span_seconds=300)
    
    # Compute signals
    metrics_engine = MetricsEngine()
    signals = metrics_engine.compute_signals(payments)
    
    logger.info(f"Success Rate: {signals.overall_success_rate:.1%}")
    
    # Reason about it
    reasoner = Reasoner()
    reasoning = await reasoner.reason(signals)
    
    logger.info(reasoning.get_summary())
    
    if "normal_operation" in reasoning.hypotheses:
        logger.info(f"\n✅ Correctly identified normal operation")


async def example_retry_storm_reasoning():
    """Example: Reasoning about retry storm."""
    logger.info("\n=== Example 5: Retry Storm Reasoning ===\n")
    
    generator = PaymentGenerator(config={"seed": 42})
    
    # High failure rate to trigger retries
    generator.base_failure_rate = 0.25
    original_payments = generator.generate_batch(count=100, time_span_seconds=300)
    
    # Add many retries
    all_payments = list(original_payments)
    for payment in original_payments:
        if payment.is_failed() and payment.should_retry():
            retries = generator.simulate_retry_storm(payment, retry_count=3)
            all_payments.extend(retries)
    
    # Compute signals
    metrics_engine = MetricsEngine()
    signals = metrics_engine.compute_signals(all_payments)
    
    logger.info(f"Total Payments: {signals.total_payments}")
    logger.info(f"Total Retries: {signals.total_retries}")
    logger.info(f"Retry Effectiveness: {signals.retry_effectiveness:+.2f}\n")
    
    # Reason about it
    reasoner = Reasoner()
    reasoning = await reasoner.reason(signals)
    
    logger.info(reasoning.get_summary())


async def example_json_export():
    """Example: Export reasoning as JSON."""
    logger.info("\n=== Example 6: JSON Export ===\n")
    
    generator = PaymentGenerator(config={"seed": 42})
    generator.simulate_bank_degradation("Axis Bank")
    payments = generator.generate_batch(count=150, time_span_seconds=300)
    
    metrics_engine = MetricsEngine()
    signals = metrics_engine.compute_signals(payments)
    
    reasoner = Reasoner()
    reasoning = await reasoner.reason(signals)
    
    # Export as JSON
    reasoning_json = json.dumps(reasoning.to_dict(), indent=2)
    
    logger.info("Reasoning as JSON:")
    logger.info(reasoning_json[:500] + "...\n")


async def example_fallback_reasoning():
    """Example: Fallback reasoning without LLM."""
    logger.info("\n=== Example 7: Fallback Reasoning (No LLM) ===\n")
    
    generator = PaymentGenerator(config={"seed": 42})
    generator.simulate_bank_degradation("SBI")
    payments = generator.generate_batch(count=100, time_span_seconds=300)
    
    metrics_engine = MetricsEngine()
    signals = metrics_engine.compute_signals(payments)
    
    # Create reasoner without API key (forces fallback)
    reasoner = Reasoner(config={"gemini_api_key": None})
    reasoning = await reasoner.reason(signals)
    
    logger.info("Using fallback reasoning (no LLM):")
    logger.info(reasoning.get_summary())


async def main():
    logger.info("Agent Reasoning Layer Examples\n")
    logger.info("=" * 60)
    
    # Check for API key
    if not os.getenv('GEMINI_API_KEY'):
        logger.warning("\n⚠️  GEMINI_API_KEY not set!")
        logger.warning("Set it in .env file or environment variable")
        logger.warning("Examples will use fallback reasoning\n")
    
    # Run all examples
    await example_basic_reasoning()
    await example_bank_degradation_reasoning()
    await example_multiple_issues_reasoning()
    await example_normal_operation_reasoning()
    await example_retry_storm_reasoning()
    await example_json_export()
    await example_fallback_reasoning()
    
    logger.info("\n" + "=" * 60)
    logger.info("=== All examples completed ===")


if __name__ == "__main__":
    asyncio.run(main())

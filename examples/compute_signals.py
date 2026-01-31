"""
Example usage of the metrics engine.

Demonstrates how to compute signals from payment data.
"""

import json
import logging
from datetime import datetime, timedelta

from simulation.generator import PaymentGenerator
from agent.metrics import MetricsEngine


# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def example_basic_signals():
    """Example: Compute basic signals from payment data."""
    logger.info("=== Example 1: Basic Signal Computation ===\n")
    
    # Generate payment data
    generator = PaymentGenerator(config={"seed": 42})
    payments = generator.generate_batch(count=100, time_span_seconds=300)
    
    # Compute signals
    engine = MetricsEngine()
    signals = engine.compute_signals(payments, window_duration_seconds=300)
    
    # Display summary
    logger.info(signals.get_summary())
    logger.info(f"\nDetailed Metrics:")
    logger.info(f"  P50 Latency: {signals.p50_latency_ms:.0f}ms")
    logger.info(f"  P95 Latency: {signals.p95_latency_ms:.0f}ms")
    logger.info(f"  P99 Latency: {signals.p99_latency_ms:.0f}ms")
    logger.info(f"  Total Retries: {signals.total_retries}")
    logger.info(f"  Retry Effectiveness: {signals.retry_effectiveness:+.2f}")


def example_bank_degradation_signals():
    """Example: Signals during bank degradation."""
    logger.info("\n=== Example 2: Bank Degradation Signals ===\n")
    
    generator = PaymentGenerator(config={"seed": 42})
    
    # Simulate HDFC Bank degradation
    generator.simulate_bank_degradation("HDFC Bank")
    
    # Generate payments
    payments = generator.generate_batch(count=200, time_span_seconds=300)
    
    # Compute signals
    engine = MetricsEngine()
    signals = engine.compute_signals(payments)
    
    logger.info(signals.get_summary())
    logger.info(f"\nBank Failure Rates:")
    for bank, rate in sorted(signals.bank_failure_rates.items(), key=lambda x: x[1], reverse=True):
        status = "🔴" if rate > 0.3 else "🟡" if rate > 0.1 else "🟢"
        logger.info(f"  {status} {bank}: {rate:.1%}")
    
    logger.info(f"\nDegraded Banks: {signals.degraded_banks}")


def example_payment_method_analysis():
    """Example: Payment method analysis."""
    logger.info("\n=== Example 3: Payment Method Analysis ===\n")
    
    generator = PaymentGenerator(config={"seed": 42})
    payments = generator.generate_batch(count=150, time_span_seconds=300)
    
    engine = MetricsEngine()
    signals = engine.compute_signals(payments)
    
    logger.info("Payment Method Performance:")
    for method, rate in signals.method_failure_rates.items():
        latency = signals.method_avg_latencies.get(method, 0)
        volume = signals.method_volumes.get(method, 0)
        logger.info(f"  {method}:")
        logger.info(f"    Volume: {volume}")
        logger.info(f"    Failure Rate: {rate:.1%}")
        logger.info(f"    Avg Latency: {latency:.0f}ms")


def example_error_distribution():
    """Example: Error distribution analysis."""
    logger.info("\n=== Example 4: Error Distribution ===\n")
    
    generator = PaymentGenerator(config={"seed": 42})
    
    # Increase failure rate to see more errors
    generator.base_failure_rate = 0.2
    payments = generator.generate_batch(count=200, time_span_seconds=300)
    
    engine = MetricsEngine()
    signals = engine.compute_signals(payments)
    
    logger.info(f"Total Errors: {signals.failed_payments}")
    logger.info(f"\nTop Errors:")
    for i, error in enumerate(signals.top_errors, 1):
        count = signals.error_code_counts.get(error, 0)
        logger.info(f"  {i}. {error}: {count} occurrences")


def example_trend_detection():
    """Example: Trend detection over multiple windows."""
    logger.info("\n=== Example 5: Trend Detection ===\n")
    
    generator = PaymentGenerator(config={"seed": 42})
    engine = MetricsEngine()
    
    # Generate multiple windows
    logger.info("Generating 5 time windows...")
    for i in range(5):
        # Gradually degrade performance
        if i > 2:
            generator.base_failure_rate = 0.1 + (i - 2) * 0.1
            generator.base_latency_ms = 200 + (i - 2) * 200
        
        payments = generator.generate_batch(count=50, time_span_seconds=60)
        signals = engine.compute_signals(payments, window_duration_seconds=60)
        
        logger.info(f"\nWindow {i+1}:")
        logger.info(f"  Success Rate: {signals.overall_success_rate:.1%}")
        logger.info(f"  Avg Latency: {signals.avg_latency_ms:.0f}ms")
        logger.info(f"  Latency Trend: {signals.latency_trend.value}")
        logger.info(f"  Failure Rate Trend: {signals.failure_rate_trend.value}")


def example_anomaly_detection():
    """Example: Anomaly detection."""
    logger.info("\n=== Example 6: Anomaly Detection ===\n")
    
    generator = PaymentGenerator(config={"seed": 42})
    
    # Simulate severe issues
    generator.simulate_bank_outage("HDFC Bank")
    generator.simulate_bank_degradation("ICICI Bank")
    
    payments = generator.generate_batch(count=200, time_span_seconds=300)
    
    engine = MetricsEngine()
    signals = engine.compute_signals(payments)
    
    if signals.has_anomaly:
        logger.info(f"🚨 ANOMALY DETECTED")
        logger.info(f"  Severity: {signals.anomaly_severity.value.upper()}")
        logger.info(f"  Description: {signals.anomaly_description}")
    else:
        logger.info("✅ No anomalies detected")
    
    logger.info(f"\nOverall Success Rate: {signals.overall_success_rate:.1%}")


def example_json_export():
    """Example: Export signals as JSON."""
    logger.info("\n=== Example 7: JSON Export ===\n")
    
    generator = PaymentGenerator(config={"seed": 42})
    payments = generator.generate_batch(count=100, time_span_seconds=300)
    
    engine = MetricsEngine()
    signals = engine.compute_signals(payments)
    
    # Convert to JSON
    signals_json = json.dumps(signals.to_dict(), indent=2)
    
    logger.info("Signals as JSON:")
    logger.info(signals_json[:500] + "...\n")  # Show first 500 chars
    
    # Optionally save to file
    # with open("data/signals.json", "w") as f:
    #     f.write(signals_json)


def example_retry_analysis():
    """Example: Retry effectiveness analysis."""
    logger.info("\n=== Example 8: Retry Analysis ===\n")
    
    generator = PaymentGenerator(config={"seed": 42})
    
    # Generate some failures
    generator.base_failure_rate = 0.15
    original_payments = generator.generate_batch(count=100, time_span_seconds=60)
    
    # Add retries for failed payments
    all_payments = list(original_payments)
    for payment in original_payments:
        if payment.is_failed() and payment.should_retry():
            retries = generator.simulate_retry_storm(payment, retry_count=2)
            all_payments.extend(retries)
    
    engine = MetricsEngine()
    signals = engine.compute_signals(all_payments)
    
    logger.info(f"Total Payments: {signals.total_payments}")
    logger.info(f"Total Retries: {signals.total_retries}")
    logger.info(f"Retry Success Rate: {signals.retry_success_rate:.1%}")
    logger.info(f"Retry Effectiveness: {signals.retry_effectiveness:+.2%}")
    
    if signals.retry_effectiveness > 0:
        logger.info("  ✅ Retries are helping!")
    else:
        logger.info("  ⚠️  Retries may not be effective")


if __name__ == "__main__":
    logger.info("Metrics Engine Examples\n")
    
    # Run all examples
    example_basic_signals()
    example_bank_degradation_signals()
    example_payment_method_analysis()
    example_error_distribution()
    example_trend_detection()
    example_anomaly_detection()
    example_json_export()
    example_retry_analysis()
    
    logger.info("\n=== All examples completed ===")

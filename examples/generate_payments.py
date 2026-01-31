"""
Example usage of the payment data generator.

This demonstrates how to generate payment data for various scenarios.
Run this file to see sample output.
"""

import json
import logging
from datetime import datetime

from simulation.generator import PaymentGenerator
from simulation.models import PaymentMethod
from simulation.scenario_configs import get_scenario, list_scenarios


# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def example_basic_generation():
    """Example: Generate basic payment data."""
    logger.info("=== Example 1: Basic Payment Generation ===")
    
    generator = PaymentGenerator()
    
    # Generate single payment
    payment = generator.generate_payment()
    logger.info(f"Generated payment: {payment.payment_id}")
    logger.info(f"  Status: {payment.status.value}")
    logger.info(f"  Amount: ₹{payment.amount}")
    logger.info(f"  Bank: {payment.bank}")
    logger.info(f"  Latency: {payment.latency_ms}ms")
    
    # Convert to JSON
    payment_json = json.dumps(payment.to_dict(), indent=2)
    logger.info(f"JSON representation:\n{payment_json}")


def example_batch_generation():
    """Example: Generate batch of payments."""
    logger.info("\n=== Example 2: Batch Payment Generation ===")
    
    generator = PaymentGenerator(config={"seed": 42})
    
    # Generate 10 payments over 60 seconds
    payments = generator.generate_batch(count=10, time_span_seconds=60)
    
    success_count = sum(1 for p in payments if p.is_successful())
    failed_count = sum(1 for p in payments if p.is_failed())
    
    logger.info(f"Generated {len(payments)} payments")
    logger.info(f"  Successful: {success_count}")
    logger.info(f"  Failed: {failed_count}")
    logger.info(f"  Success rate: {success_count/len(payments)*100:.1f}%")


def example_bank_degradation():
    """Example: Simulate bank degradation."""
    logger.info("\n=== Example 3: Bank Degradation Scenario ===")
    
    generator = PaymentGenerator(config={"seed": 42})
    
    # Normal operation
    logger.info("Generating payments during normal operation...")
    normal_payments = generator.generate_batch(count=20, time_span_seconds=30)
    normal_success_rate = sum(1 for p in normal_payments if p.is_successful()) / len(normal_payments)
    
    # Degrade HDFC Bank
    generator.simulate_bank_degradation("HDFC Bank")
    
    logger.info("Generating payments during HDFC Bank degradation...")
    degraded_payments = generator.generate_batch(count=20, time_span_seconds=30)
    degraded_success_rate = sum(1 for p in degraded_payments if p.is_successful()) / len(degraded_payments)
    
    logger.info(f"Normal success rate: {normal_success_rate*100:.1f}%")
    logger.info(f"Degraded success rate: {degraded_success_rate*100:.1f}%")
    
    # Show bank health
    health = generator.get_bank_health_summary()
    logger.info("\nBank Health Summary:")
    for bank, status in health.items():
        logger.info(f"  {bank}: {status}")


def example_retry_storm():
    """Example: Simulate retry storm."""
    logger.info("\n=== Example 4: Retry Storm Scenario ===")
    
    generator = PaymentGenerator(config={"seed": 42})
    
    # Generate a failed payment
    failed_payment = generator.generate_payment(force_failure=True)
    logger.info(f"Original payment: {failed_payment.payment_id}")
    logger.info(f"  Status: {failed_payment.status.value}")
    logger.info(f"  Error: {failed_payment.error_code.value}")
    
    # Generate retries
    if failed_payment.should_retry():
        retries = generator.simulate_retry_storm(failed_payment, retry_count=3)
        logger.info(f"\nGenerated {len(retries)} retry attempts:")
        for retry in retries:
            logger.info(f"  Retry {retry.retry_count}: {retry.timestamp.isoformat()} - {retry.status.value}")


def example_payment_methods():
    """Example: Generate payments for different methods."""
    logger.info("\n=== Example 5: Different Payment Methods ===")
    
    generator = PaymentGenerator(config={"seed": 42})
    
    for method in PaymentMethod:
        payment = generator.generate_payment(payment_method=method)
        logger.info(f"{method.value}: ₹{payment.amount} - {payment.status.value}")


def example_scenario_config():
    """Example: Use pre-defined scenario configuration."""
    logger.info("\n=== Example 6: Using Scenario Configurations ===")
    
    logger.info("Available scenarios:")
    for scenario_name in list_scenarios():
        scenario = get_scenario(scenario_name)
        logger.info(f"  - {scenario.name}: {scenario.description}")
    
    # Use a specific scenario
    scenario = get_scenario("bank_degradation")
    logger.info(f"\nUsing scenario: {scenario.name}")
    
    generator = PaymentGenerator(config=scenario.config)
    
    # Apply scenario-specific settings
    if "degraded_banks" in scenario.config:
        for bank in scenario.config["degraded_banks"]:
            generator.simulate_bank_degradation(bank)
    
    payments = generator.generate_batch(count=20, time_span_seconds=60)
    success_rate = sum(1 for p in payments if p.is_successful()) / len(payments)
    
    logger.info(f"Generated {len(payments)} payments")
    logger.info(f"Success rate: {success_rate*100:.1f}%")


def example_export_to_json():
    """Example: Export payments to JSON file."""
    logger.info("\n=== Example 7: Export to JSON ===")
    
    generator = PaymentGenerator(config={"seed": 42})
    payments = generator.generate_batch(count=50, time_span_seconds=120)
    
    # Convert to JSON
    payments_data = [p.to_dict() for p in payments]
    
    output_file = "data/sample_payments.json"
    with open(output_file, 'w') as f:
        json.dump(payments_data, f, indent=2)
    
    logger.info(f"Exported {len(payments)} payments to {output_file}")


if __name__ == "__main__":
    logger.info("Payment Data Generator Examples\n")
    
    # Run all examples
    example_basic_generation()
    example_batch_generation()
    example_bank_degradation()
    example_retry_storm()
    example_payment_methods()
    example_scenario_config()
    # example_export_to_json()  # Uncomment to export to file
    
    logger.info("\n=== All examples completed ===")

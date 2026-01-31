"""
Configuration for payment simulation scenarios.

Defines various realistic scenarios that can be simulated.
"""

from typing import Dict, Any, List
from dataclasses import dataclass


@dataclass
class ScenarioConfig:
    """Configuration for a simulation scenario."""
    name: str
    description: str
    duration_seconds: int
    config: Dict[str, Any]


# Pre-defined realistic scenarios
SCENARIOS = {
    "normal": ScenarioConfig(
        name="Normal Operations",
        description="Typical payment processing with ~95% success rate",
        duration_seconds=300,
        config={
            "base_failure_rate": 0.05,
            "base_latency_ms": 200,
            "enable_scenarios": False
        }
    ),
    
    "bank_degradation": ScenarioConfig(
        name="Bank Degradation",
        description="One bank experiencing degraded performance",
        duration_seconds=600,
        config={
            "base_failure_rate": 0.05,
            "base_latency_ms": 200,
            "enable_scenarios": True,
            "degraded_banks": ["HDFC Bank"],
            "degradation_duration": 600
        }
    ),
    
    "bank_outage": ScenarioConfig(
        name="Bank Outage",
        description="Complete outage of one bank",
        duration_seconds=900,
        config={
            "base_failure_rate": 0.05,
            "base_latency_ms": 200,
            "enable_scenarios": True,
            "down_banks": ["State Bank of India"],
            "outage_duration": 900
        }
    ),
    
    "high_latency": ScenarioConfig(
        name="High Latency Period",
        description="Network issues causing high latency across all banks",
        duration_seconds=300,
        config={
            "base_failure_rate": 0.08,
            "base_latency_ms": 800,  # 4x normal
            "enable_scenarios": True
        }
    ),
    
    "retry_storm": ScenarioConfig(
        name="Retry Storm",
        description="High failure rate causing many retries",
        duration_seconds=180,
        config={
            "base_failure_rate": 0.25,  # 25% failure rate
            "base_latency_ms": 300,
            "enable_scenarios": True,
            "retry_probability": 0.8  # 80% of failures get retried
        }
    ),
    
    "upi_issues": ScenarioConfig(
        name="UPI Payment Issues",
        description="Specific issues with UPI payment method",
        duration_seconds=450,
        config={
            "base_failure_rate": 0.05,
            "base_latency_ms": 200,
            "enable_scenarios": True,
            "payment_method_failures": {
                "UPI": 0.20  # 20% failure rate for UPI
            }
        }
    ),
    
    "multi_bank_issues": ScenarioConfig(
        name="Multiple Bank Issues",
        description="Several banks experiencing problems simultaneously",
        duration_seconds=1200,
        config={
            "base_failure_rate": 0.05,
            "base_latency_ms": 200,
            "enable_scenarios": True,
            "degraded_banks": ["ICICI Bank", "Axis Bank"],
            "down_banks": ["Yes Bank"]
        }
    ),
    
    "peak_load": ScenarioConfig(
        name="Peak Load",
        description="High transaction volume with increased failures",
        duration_seconds=600,
        config={
            "base_failure_rate": 0.12,  # Higher failure rate
            "base_latency_ms": 400,     # Higher latency
            "enable_scenarios": True,
            "transaction_rate_multiplier": 3.0  # 3x normal volume
        }
    )
}


def get_scenario(scenario_name: str) -> ScenarioConfig:
    """
    Get a scenario configuration by name.
    
    Args:
        scenario_name: Name of the scenario
        
    Returns:
        Scenario configuration
        
    Raises:
        KeyError: If scenario not found
    """
    if scenario_name not in SCENARIOS:
        available = ", ".join(SCENARIOS.keys())
        raise KeyError(
            f"Scenario '{scenario_name}' not found. "
            f"Available scenarios: {available}"
        )
    
    return SCENARIOS[scenario_name]


def list_scenarios() -> List[str]:
    """
    List all available scenario names.
    
    Returns:
        List of scenario names
    """
    return list(SCENARIOS.keys())


def get_scenario_description(scenario_name: str) -> str:
    """
    Get description of a scenario.
    
    Args:
        scenario_name: Name of the scenario
        
    Returns:
        Scenario description
    """
    scenario = get_scenario(scenario_name)
    return f"{scenario.name}: {scenario.description}"

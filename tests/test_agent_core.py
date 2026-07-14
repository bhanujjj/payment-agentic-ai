"""
Unit tests for PaymentAgent core lifecycle and step loop.
"""

import tempfile
from pathlib import Path
import pytest
from datetime import datetime, timedelta

from agent.core import PaymentAgent
from simulation.models import PaymentRecord, PaymentStatus, PaymentMethod, ErrorCode
from agent.signals import PaymentSignals
from agent.decision_models import Decision
from agent.execution_models import ExecutionResult


@pytest.fixture
def temp_memory_file():
    with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as temp:
        path = temp.name
    yield path
    # Cleanup
    p = Path(path)
    if p.exists():
        p.unlink()


def create_mock_payments(count=10, failed_count=0, bank="HDFC Bank"):
    payments = []
    base_time = datetime.utcnow()
    for i in range(count):
        is_fail = i < failed_count
        payments.append(PaymentRecord(
            payment_id=f"tx_{i}",
            timestamp=base_time + timedelta(seconds=i),
            payment_method=PaymentMethod.UPI,
            bank=bank,
            amount=100.0,
            currency="INR",
            status=PaymentStatus.FAILED if is_fail else PaymentStatus.SUCCESS,
            error_code=ErrorCode.BANK_TIMEOUT if is_fail else ErrorCode.NONE,
            latency_ms=3000 if is_fail else 150,
            retry_count=0
        ))
    return payments


def test_agent_initialization(temp_memory_file):
    config = {
        "memory": {"path": temp_memory_file},
        "decision": {
            "min_confidence": 0.8
        }
    }
    agent = PaymentAgent(config=config)
    assert agent.metrics_engine is not None
    assert agent.reasoner is not None
    assert agent.decider is not None
    assert agent.executor is not None
    assert agent.evaluator is not None
    assert str(agent.memory.storage_path) == temp_memory_file


@pytest.mark.asyncio
async def test_agent_run_step_normal(temp_memory_file):
    config = {
        "memory": {"path": temp_memory_file}
    }
    agent = PaymentAgent(config=config)
    
    payments = create_mock_payments(count=10, failed_count=0)
    
    res = await agent.run_step(payments)
    
    assert "signals" in res
    assert "reasoning" in res
    assert "decision" in res
    assert "execution" in res
    assert "learning" in res
    
    assert isinstance(res["signals"], PaymentSignals)
    assert isinstance(res["decision"], Decision)
    assert isinstance(res["execution"], ExecutionResult)
    
    # Normal operation should lead to do_nothing or alert_ops
    assert res["decision"].selected_action in ["do_nothing", "alert_ops"]


@pytest.mark.asyncio
async def test_agent_learning_loop(temp_memory_file):
    config = {
        "memory": {"path": temp_memory_file}
    }
    agent = PaymentAgent(config=config)
    
    # Step 1: Degraded performance, agent should pick an action (e.g. recommend_reroute)
    payments_degraded = create_mock_payments(count=20, failed_count=15, bank="HDFC Bank")
    res1 = await agent.run_step(payments_degraded)
    
    # Store the signals and action taken
    sig1 = res1["signals"]
    act1 = res1["decision"].selected_action
    
    assert act1 != "do_nothing"
    
    # Step 2: System recovers, running step 2 should trigger learning for Step 1 action
    payments_recovered = create_mock_payments(count=20, failed_count=1, bank="HDFC Bank")
    res2 = await agent.run_step(payments_recovered, prev_signals=sig1, prev_action=act1)
    
    assert res2["learning"] is not None
    assert res2["learning"]["action"] == act1
    assert res2["learning"]["success"] is True

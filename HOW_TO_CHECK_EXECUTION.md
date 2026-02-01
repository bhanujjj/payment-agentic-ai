# How to Check Action Execution (Step 6)

## Quick Verification

### 1. Run Unit Tests
```bash
pytest tests/test_executor.py -v
```

**Expected**: All tests pass ✅

---

### 2. Run Examples
```bash
PYTHONPATH=. python examples/action_execution.py
```

**What to Look For**:
- ✅ Example 1: `do_nothing` executes
- ✅ Example 2: `alert_ops` executes with state changes
- ✅ Example 3: Action blocked for approval
- ✅ Example 4: System state updated correctly
- ✅ Example 5: JSON export works

---

## Detailed Verification

### Test 1: Approval Guardrails

**Command**:
```bash
python -c "
import asyncio
from simulation.generator import PaymentGenerator
from agent.metrics import MetricsEngine
from agent.reasoner import Reasoner
from agent.decider import DecisionEngine
from agent.executor import ActionExecutor

async def test():
    # Critical scenario
    gen = PaymentGenerator(config={'seed': 42})
    gen.simulate_bank_outage('HDFC Bank')
    gen.simulate_bank_outage('ICICI Bank')
    payments = gen.generate_batch(count=200, time_span_seconds=300)
    
    engine = MetricsEngine()
    signals = engine.compute_signals(payments)
    
    reasoner = Reasoner()
    reasoning = await reasoner.reason(signals)
    
    decider = DecisionEngine()
    decision = decider.decide(reasoning, signals)
    
    executor = ActionExecutor()
    result = executor.execute(decision, signals)
    
    print(f'Decision: {decision.selected_action}')
    print(f'Requires Approval: {decision.requires_human_approval}')
    print(f'Executed: {result.executed}')
    print(f'Status: {result.status.value}')
    
    if result.status.value == 'PENDING_HUMAN_APPROVAL':
        print('✅ PASS: High-risk action blocked for approval')
    else:
        print('❌ FAIL: Should have blocked for approval')

asyncio.run(test())
"
```

**Expected**: Action blocked with `PENDING_HUMAN_APPROVAL` ✅

---

### Test 2: State Changes

**Command**:
```bash
python -c "
import asyncio
from simulation.generator import PaymentGenerator
from agent.metrics import MetricsEngine
from agent.reasoner import Reasoner
from agent.decider import DecisionEngine
from agent.executor import ActionExecutor

async def test():
    gen = PaymentGenerator(config={'seed': 42})
    gen.simulate_bank_degradation('HDFC Bank')
    payments = gen.generate_batch(count=200, time_span_seconds=300)
    
    engine = MetricsEngine()
    signals = engine.compute_signals(payments)
    
    reasoner = Reasoner()
    reasoning = await reasoner.reason(signals)
    
    decider = DecisionEngine()
    decision = decider.decide(reasoning, signals)
    
    # Force execution for testing
    decision.requires_human_approval = False
    
    executor = ActionExecutor()
    result = executor.execute(decision, signals)
    
    print(f'Action: {result.action}')
    print(f'Executed: {result.executed}')
    print(f'State Changes: {result.state_changes}')
    
    state = executor.get_state()
    print(f'System State:')
    print(f'  Routing: {state.routing_overrides}')
    print(f'  Alerts: {len(state.alerts)}')
    print(f'  Last Action: {state.last_action}')
    
    if result.executed and len(result.state_changes) > 0:
        print('✅ PASS: State changes recorded')
    else:
        print('❌ FAIL: No state changes')

asyncio.run(test())
"
```

**Expected**: State changes visible ✅

---

### Test 3: Full Pipeline

**Command**:
```bash
python -c "
import asyncio
from simulation.generator import PaymentGenerator
from agent.metrics import MetricsEngine
from agent.reasoner import Reasoner
from agent.decider import DecisionEngine
from agent.executor import ActionExecutor

async def test():
    print('FULL PIPELINE TEST')
    print('=' * 60)
    
    # Setup
    gen = PaymentGenerator(config={'seed': 42})
    gen.simulate_bank_degradation('HDFC Bank')
    gen.simulate_bank_degradation('ICICI Bank')
    
    # Generate data
    payments = gen.generate_batch(count=200, time_span_seconds=300)
    print(f'✅ Generated {len(payments)} payments')
    
    # Compute signals
    engine = MetricsEngine()
    signals = engine.compute_signals(payments)
    print(f'✅ Computed signals: {signals.overall_success_rate:.1%} success')
    
    # Reason
    reasoner = Reasoner()
    reasoning = await reasoner.reason(signals)
    print(f'✅ Reasoning: {reasoning.get_top_hypothesis()}')
    
    # Decide
    decider = DecisionEngine()
    decision = decider.decide(reasoning, signals)
    print(f'✅ Decision: {decision.selected_action} ({decision.confidence:.0%})')
    
    # Execute
    executor = ActionExecutor()
    result = executor.execute(decision, signals)
    print(f'✅ Execution: {result.status.value}')
    
    print('=' * 60)
    print('FULL PIPELINE: SUCCESS ✅')

asyncio.run(test())
"
```

**Expected**: All steps complete successfully ✅

---

## What Each Action Does

### `do_nothing`
- **Execution**: Always succeeds
- **State Changes**: None
- **Use Case**: Monitoring only

### `alert_ops`
- **Execution**: Always succeeds
- **State Changes**: Adds alert to `state.alerts`
- **Use Case**: Notify operations team

### `recommend_path_suppression`
- **Execution**: May require approval
- **State Changes**: Updates `state.routing_overrides`
- **Use Case**: Suppress degraded banks

### `recommend_reroute`
- **Execution**: May require approval
- **State Changes**: Updates `state.routing_overrides`
- **Use Case**: Reroute traffic away from issues

### `recommend_circuit_breaker`
- **Execution**: May require approval
- **State Changes**: Updates `state.circuit_breakers`
- **Use Case**: Prevent cascading failures

### `recommend_retry_adjustment`
- **Execution**: Usually auto-executes
- **State Changes**: Updates `state.retry_policy`
- **Use Case**: Prevent retry storms

---

## Troubleshooting

### Issue: All actions blocked
**Cause**: All decisions require approval
**Fix**: Check decision engine risk assessment

### Issue: No state changes
**Cause**: Actions not executing
**Fix**: Check `result.executed` and `result.error`

### Issue: Tests failing
**Cause**: Import errors or missing dependencies
**Fix**: Run `pytest tests/test_executor.py -v` for details

---

## Success Criteria

✅ All unit tests pass
✅ Examples run without errors
✅ Approval blocking works
✅ State changes are recorded
✅ JSON export works
✅ Full pipeline executes

---

**Status**: Step 6 Complete

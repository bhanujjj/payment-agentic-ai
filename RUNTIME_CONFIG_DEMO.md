# Runtime Configuration Change Demo

## Overview

This demo shows the agent making a **REAL runtime configuration change** in response to a retry storm scenario.

## What It Demonstrates

1. **Scenario Detection**: Agent detects retry storm (high retry rate, low effectiveness)
2. **Decision Making**: Selects `recommend_retry_adjustment` action
3. **Guardrail Check**: Risk level is LOW, no approval required
4. **Execution**: Agent modifies retry policy at runtime
5. **State Update**: System configuration is updated in memory
6. **Verification**: Before/after comparison shows the change

## Running the Demo

```bash
PYTHONPATH=. python examples/runtime_config_demo.py
```

## Expected Output

### Key Sections

**STEP 1: Initial Configuration**
```
Initial Retry Policy: {'max_retries': 3, 'backoff_ms': 1000}
```

**STEP 2: Retry Storm Scenario**
```
Generated 200 original payments
Generated 15 retry attempts
Retry rate: 7.5%
Retry Effectiveness: -0.92  (negative = harmful)
```

**STEP 5: Decision**
```
Selected Action: recommend_retry_adjustment
Risk Level: LOW
Requires Approval: False
```

**STEP 6: Execution**
```
BEFORE Execution:
  Retry Policy: {'max_retries': 3, 'backoff_ms': 1000}

Execution Status: EXECUTED
Executed: True

AFTER Execution:
  Retry Policy: {'max_retries': 2, 'backoff_ms': 1000}
```

**STEP 8: Verification**
```
Before: max_retries = 3
After:  max_retries = 2

✅ Runtime configuration successfully updated by agent
   Retry limit reduced from 3 to 2
   This will prevent retry storms in future payments
```

## What Changed

### Runtime Configuration
- **Before**: `max_retries: 3`
- **After**: `max_retries: 2`

### System State
The `SystemState` object is updated:
```python
executor.system_state.retry_policy = {
    'max_retries': 2,  # Changed from 3
    'backoff_ms': 1000
}
```

### Execution Result
```python
ExecutionResult(
    action='recommend_retry_adjustment',
    executed=True,
    status=ExecutionStatus.EXECUTED,
    impact_scope='retry_policy',
    expected_effect='Set max retries to 2 for balanced reliability',
    state_changes={'retry_policy': {'max_retries': 2, 'backoff_ms': 1000}}
)
```

## Why This Matters

1. **No Approval Required**: Low-risk action executes automatically
2. **Real State Change**: Configuration is actually modified
3. **Logged Clearly**: All changes are visible in output
4. **Reversible**: Can be reset via `executor.reset_state()`
5. **Production-Ready**: Same pattern works for real systems

## Implementation Details

### Action Handler
Located in `agent/executor.py`:

```python
def _execute_recommend_retry_adjustment(self, decision, signals):
    # Reduce retries if retry storm detected
    if signals.total_retries > signals.total_payments * 0.5:
        self.system_state.retry_policy["max_retries"] = 1
        effect = "Reduced max retries to 1 to prevent retry storm"
    else:
        self.system_state.retry_policy["max_retries"] = 2
        effect = "Set max retries to 2 for balanced reliability"
    
    self.system_state.last_action = "recommend_retry_adjustment"
    self.system_state.last_updated = datetime.utcnow()
    
    return ExecutionResult(
        action="recommend_retry_adjustment",
        executed=True,
        status=ExecutionStatus.EXECUTED,
        impact_scope="retry_policy",
        expected_effect=effect,
        state_changes={"retry_policy": dict(self.system_state.retry_policy)}
    )
```

### Guardrails
- Risk assessment: `RiskLevel.LOW`
- Approval required: `False`
- Reversibility: `executor.reset_state()`

## Use Cases

This pattern applies to:
- ✅ Retry policy adjustments
- ✅ Rate limit changes
- ✅ Timeout modifications
- ✅ Circuit breaker thresholds
- ✅ Routing weight updates

## Constraints

- ❌ Does NOT modify source code
- ❌ Does NOT bypass guardrails
- ❌ Does NOT change payment processing logic
- ✅ ONLY updates runtime configuration

## Next Steps

For production deployment:
1. Persist state changes to database
2. Add rollback mechanism
3. Log all config changes for audit
4. Monitor impact of changes
5. Build approval workflow for higher-risk actions

---

**Status**: ✅ Demo Complete  
**Runtime Config Change**: ✅ Verified  
**Execution**: ✅ Automatic (no approval)  
**State Update**: ✅ Confirmed

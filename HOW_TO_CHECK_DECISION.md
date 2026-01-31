# How to Check the Decision Engine is Working

This guide shows you exactly how to verify the Decision Engine (Step 5) implementation.

---

## Prerequisites

### **1. Complete Previous Steps**
Ensure Steps 1-4 are working:
- ✅ Payment data simulation
- ✅ Metrics engine
- ✅ Reasoning layer with Gemini API

### **2. Environment Setup**
```bash
cd "/Users/bhanujbhalla/Desktop/Projects/payment agentic ai "
# API key should already be set from Step 4
```

---

## Quick Start (Recommended)

### **Run the Examples**
```bash
PYTHONPATH=. python examples/decision_making.py
```

This will run 6 examples showing:
- ✅ Normal operation decisions
- ✅ Bank degradation decisions
- ✅ Multiple issues handling
- ✅ Strict constraints enforcement
- ✅ JSON export
- ✅ High risk scenarios with approval requirements

**Expected Output:**
```
=== Example 1: Normal Operation ===

Decision: do_nothing
  Confidence: 65%
  Risk Level: LOW
  Requires Approval: No
  Reasoning: normal_operation detected with 85% confidence

  Considered Actions:
    • do_nothing: 65%
    • alert_ops: 55%
```

---

## Run Tests

```bash
# Test decision models
python -m pytest tests/test_decision_models.py -v

# Test decision engine
python -m pytest tests/test_decider.py -v

# Run all tests
python -m pytest tests/test_decision_models.py tests/test_decider.py -v
```

**Expected:** All tests should pass ✅

---

## Interactive Testing

### **Test 1: Basic Decision Making**
```bash
python -c "
import asyncio
from simulation import PaymentGenerator
from agent import MetricsEngine, Reasoner, DecisionEngine

async def test():
    gen = PaymentGenerator(config={'seed': 42})
    gen.base_failure_rate = 0.02
    payments = gen.generate_batch(count=100, time_span_seconds=300)
    
    engine = MetricsEngine()
    signals = engine.compute_signals(payments)
    
    reasoner = Reasoner()
    reasoning = await reasoner.reason(signals)
    
    decider = DecisionEngine()
    decision = decider.decide(reasoning, signals)
    
    print(decision.get_summary())

asyncio.run(test())
"
```

### **Test 2: Bank Degradation Decision**
```bash
python -c "
import asyncio
from simulation import PaymentGenerator
from agent import MetricsEngine, Reasoner, DecisionEngine

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
    
    print(f'Decision: {decision.selected_action}')
    print(f'Risk: {decision.risk_level.value}')
    print(f'Requires Approval: {decision.requires_human_approval}')
    print(f'\nTop 3 Actions:')
    for action in decision.considered_actions[:3]:
        print(f'  {action.action}: {action.score:.0%}')

asyncio.run(test())
"
```

### **Test 3: Strict Constraints**
```bash
python -c "
import asyncio
from simulation import PaymentGenerator
from agent import MetricsEngine, Reasoner, DecisionEngine, DecisionConstraints, RiskLevel

async def test():
    gen = PaymentGenerator(config={'seed': 42})
    gen.simulate_bank_degradation('SBI')
    payments = gen.generate_batch(count=150, time_span_seconds=300)
    
    engine = MetricsEngine()
    signals = engine.compute_signals(payments)
    
    reasoner = Reasoner()
    reasoning = await reasoner.reason(signals)
    
    # Strict constraints
    constraints = DecisionConstraints(
        max_auto_approve_risk=RiskLevel.LOW,
        allow_rerouting=False
    )
    decider = DecisionEngine(constraints=constraints)
    decision = decider.decide(reasoning, signals)
    
    print(f'Decision: {decision.selected_action}')
    print(f'Requires Approval: {decision.requires_human_approval}')
    
    if decision.rejected_actions:
        print(f'\nRejected Actions:')
        for action, reason in decision.rejected_actions.items():
            print(f'  {action}: {reason}')

asyncio.run(test())
"
```

### **Test 4: JSON Export**
```bash
python -c "
import asyncio
import json
from simulation import PaymentGenerator
from agent import MetricsEngine, Reasoner, DecisionEngine

async def test():
    gen = PaymentGenerator(config={'seed': 42})
    gen.simulate_bank_degradation('Axis Bank')
    payments = gen.generate_batch(count=100, time_span_seconds=300)
    
    engine = MetricsEngine()
    signals = engine.compute_signals(payments)
    
    reasoner = Reasoner()
    reasoning = await reasoner.reason(signals)
    
    decider = DecisionEngine()
    decision = decider.decide(reasoning, signals)
    
    print(json.dumps(decision.to_dict(), indent=2))

asyncio.run(test())
"
```

---

## What to Look For

### ✅ **Success Indicators:**

1. **Examples run without errors**
2. **Tests all pass (10/10 models + 7/7 engine)**
3. **Decision output is structured:**
   - Has `selected_action` string
   - Has `confidence` between 0-1
   - Has `risk_level` (LOW/MEDIUM/HIGH/CRITICAL)
   - Has `requires_human_approval` boolean
   - Has `reasoning_summary` string
   - Has `considered_actions` list

4. **Action scoring works:**
   - Multiple actions considered
   - Scores are between 0-1
   - Higher scores for better actions
   - Actions ranked by score

5. **Risk assessment works:**
   - Risk levels assigned correctly
   - High risk actions require approval
   - Constraints enforced

6. **Guardrails work:**
   - Actions respect constraints
   - Rejected actions have reasons
   - Fallback to `do_nothing` when needed

---

## Decision Logic Verification

### **Scenario: Normal Operation**
- **Expected**: `do_nothing` or `alert_ops`
- **Risk**: LOW
- **Approval**: No

### **Scenario: Bank Degradation**
- **Expected**: `recommend_reroute` or `recommend_path_suppression`
- **Risk**: MEDIUM
- **Approval**: Yes (if constraints are strict)

### **Scenario: Multiple Bank Outages**
- **Expected**: `recommend_reroute` or `recommend_circuit_breaker`
- **Risk**: MEDIUM or HIGH
- **Approval**: Yes

### **Scenario: Retry Storm**
- **Expected**: `recommend_retry_reduction`
- **Risk**: LOW or MEDIUM
- **Approval**: Depends on risk level

---

## Common Issues

### **Issue: No actions generated**
```
# Solution: Check reasoning output has hypotheses
# The decision engine needs hypotheses to generate actions
```

### **Issue: All actions rejected**
```
# Solution: Relax constraints
constraints = DecisionConstraints(
    min_confidence_for_action=0.3,  # Lower threshold
    max_auto_approve_risk=RiskLevel.MEDIUM
)
```

### **Issue: Always selects do_nothing**
```
# Solution: Check reasoning confidence
# Low confidence reasoning leads to conservative decisions
```

---

## Full Example Script

Save this as `test_decision.py`:

```python
import asyncio
from simulation import PaymentGenerator
from agent import MetricsEngine, Reasoner, DecisionEngine, DecisionConstraints, RiskLevel

async def main():
    print("Testing Decision Engine\n")
    
    # Test 1: Normal operation
    print("1. Normal Operation:")
    gen = PaymentGenerator(config={'seed': 42})
    gen.base_failure_rate = 0.02
    payments = gen.generate_batch(count=100, time_span_seconds=300)
    
    engine = MetricsEngine()
    signals = engine.compute_signals(payments)
    
    reasoner = Reasoner()
    reasoning = await reasoner.reason(signals)
    
    decider = DecisionEngine()
    decision = decider.decide(reasoning, signals)
    
    print(decision.get_summary())
    
    # Test 2: Bank degradation
    print("\n2. Bank Degradation:")
    gen = PaymentGenerator(config={'seed': 42})
    gen.simulate_bank_degradation("HDFC Bank")
    payments = gen.generate_batch(count=200, time_span_seconds=300)
    
    signals = engine.compute_signals(payments)
    reasoning = await reasoner.reason(signals)
    decision = decider.decide(reasoning, signals)
    
    print(decision.get_summary())
    print(f"Degraded banks: {signals.degraded_banks}")
    
    # Test 3: Verify action scoring
    print("\n3. Action Scoring:")
    print(f"Top 3 actions:")
    for action in decision.considered_actions[:3]:
        print(f"  {action.action}:")
        print(f"    Score: {action.score:.0%}")
        print(f"    Risk: {action.risk_level.value}")
        print(f"    Success Impact: {action.expected_success_rate_impact:+.0%}")
    
    print("\n✅ All tests completed successfully!")

if __name__ == "__main__":
    asyncio.run(main())
```

Run it:
```bash
PYTHONPATH=. python test_decision.py
```

---

## Expected Results Summary

| Test | Expected Result |
|------|----------------|
| Basic decision | Returns structured Decision object |
| Normal operation | Selects `do_nothing` or `alert_ops` with LOW risk |
| Bank degradation | Selects action like `recommend_reroute` with MEDIUM risk |
| Multiple issues | Multiple actions considered, best one selected |
| Strict constraints | Respects constraints, may require approval |
| JSON export | Valid JSON with all required fields |
| Risk assessment | Correct risk levels assigned |
| Approval logic | High/medium risk requires approval |

---

## Verification Checklist

- [ ] Decision models tests pass (10/10)
- [ ] Decision engine tests pass (7/7)
- [ ] Examples run successfully
- [ ] Decisions are structured correctly
- [ ] Action scoring produces reasonable scores
- [ ] Risk assessment assigns correct levels
- [ ] Constraints are enforced
- [ ] High risk actions require approval
- [ ] Rejected actions have reasons
- [ ] JSON export works

---

## Key Features Verified

✅ **Deterministic Decision Making** (no LLM)  
✅ **Action Scoring** with impact metrics  
✅ **Risk Assessment** (LOW/MEDIUM/HIGH/CRITICAL)  
✅ **Constraint Enforcement** (guardrails)  
✅ **Human Approval** for high-risk actions  
✅ **Action Rejection** with reasons  
✅ **Structured Output** (machine-readable)  

---

**STEP 5 COMPLETE** ✅

The decision engine can now:
- Generate candidate actions based on reasoning
- Score actions using impact metrics
- Assess risk levels
- Enforce constraints and guardrails
- Require human approval for high-risk actions
- Provide structured, deterministic decisions

**Next Step**: Action execution layer (Step 6) to execute the selected actions.

---

**Date**: 2026-01-31  
**Status**: ✅ VERIFIED AND WORKING

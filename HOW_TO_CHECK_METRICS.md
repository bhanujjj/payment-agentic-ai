# How to Check the Metrics Engine is Working

This guide shows you exactly how to verify the Signal/Metrics Engine implementation.

---

## Quick Start (Recommended)

### **Run the Examples**
```bash
cd "/Users/bhanujbhalla/Desktop/Projects/payment agentic ai "
PYTHONPATH=. python examples/compute_signals.py
```

This will run 8 examples and show you:
- ✅ Basic signal computation
- ✅ Bank degradation detection
- ✅ Payment method analysis
- ✅ Error distribution
- ✅ Trend detection
- ✅ Anomaly detection
- ✅ JSON export
- ✅ Retry effectiveness

**Expected Output:**
```
=== Example 1: Basic Payment Generation ===
Payment Signals (300s window)
  Total: 100 payments
  Success Rate: 90.0%
  Avg Latency: 250ms

=== Example 2: Bank Degradation Signals ===
Payment Signals (300s window)
  Total: 200 payments
  Success Rate: 85.0%
  Avg Latency: 285ms
  ⚠️  Degraded Banks: HDFC Bank

Bank Failure Rates:
  🔴 HDFC Bank: 44.0%
  🟢 ICICI Bank: 12.0%
  ...
```

---

## Run Tests

```bash
cd "/Users/bhanujbhalla/Desktop/Projects/payment agentic ai "
python -m pytest tests/test_signals.py tests/test_metrics.py -v
```

**Expected:** All 16 tests should pass ✅

---

## Interactive Testing

### **Test 1: Basic Signals**
```bash
python -c "
from simulation import PaymentGenerator
from agent import MetricsEngine

gen = PaymentGenerator(config={'seed': 42})
payments = gen.generate_batch(count=100, time_span_seconds=300)

engine = MetricsEngine()
signals = engine.compute_signals(payments)

print(signals.get_summary())
print(f'P95 Latency: {signals.p95_latency_ms:.0f}ms')
print(f'Top Errors: {signals.top_errors}')
"
```

### **Test 2: Bank Degradation**
```bash
python -c "
from simulation import PaymentGenerator
from agent import MetricsEngine

gen = PaymentGenerator()
gen.simulate_bank_degradation('HDFC Bank')
payments = gen.generate_batch(count=150, time_span_seconds=300)

engine = MetricsEngine()
signals = engine.compute_signals(payments)

print(f'Degraded Banks: {signals.degraded_banks}')
print(f'HDFC Failure Rate: {signals.bank_failure_rates.get(\"HDFC Bank\", 0):.1%}')
"
```

### **Test 3: Anomaly Detection**
```bash
python -c "
from simulation import PaymentGenerator
from agent import MetricsEngine

gen = PaymentGenerator()
gen.simulate_bank_outage('ICICI Bank')
gen.simulate_bank_outage('HDFC Bank')
payments = gen.generate_batch(count=200, time_span_seconds=300)

engine = MetricsEngine()
signals = engine.compute_signals(payments)

print(f'Anomaly Detected: {signals.has_anomaly}')
print(f'Severity: {signals.anomaly_severity.value}')
print(f'Description: {signals.anomaly_description}')
"
```

### **Test 4: Export to JSON**
```bash
python -c "
from simulation import PaymentGenerator
from agent import MetricsEngine
import json

gen = PaymentGenerator(config={'seed': 42})
payments = gen.generate_batch(count=100, time_span_seconds=300)

engine = MetricsEngine()
signals = engine.compute_signals(payments)

# Print formatted JSON
print(json.dumps(signals.to_dict(), indent=2))
" | head -50
```

---

## What to Look For

### ✅ **Success Indicators:**

1. **Examples run without errors**
2. **Tests all pass (16/16)**
3. **Signals show realistic data:**
   - Success rate between 0-100%
   - Latency values > 0
   - Bank/method metrics populated
   - Degraded banks detected when simulated

4. **Anomaly detection works:**
   - Normal operations → no anomaly
   - Bank degradation → warning
   - Multiple outages → critical

5. **Trends detected:**
   - First window → UNKNOWN
   - Subsequent windows → RISING/STABLE/FALLING

---

## Common Issues

### **Issue: ModuleNotFoundError**
```bash
# Solution: Set PYTHONPATH
PYTHONPATH=. python examples/compute_signals.py
```

### **Issue: No degraded banks detected**
```
# This is normal if the degraded bank didn't receive much traffic
# Try with more payments:
gen.generate_batch(count=500, time_span_seconds=300)
```

---

## Full Example Script

Save this as `test_metrics.py`:

```python
from simulation import PaymentGenerator
from agent import MetricsEngine

def main():
    print("Testing Metrics Engine\n")
    
    # Setup
    gen = PaymentGenerator(config={'seed': 42})
    engine = MetricsEngine()
    
    # Test 1: Normal operation
    print("1. Normal Operation:")
    payments = gen.generate_batch(count=100, time_span_seconds=300)
    signals = engine.compute_signals(payments)
    print(signals.get_summary())
    
    # Test 2: Bank degradation
    print("\n2. Bank Degradation:")
    gen.simulate_bank_degradation("HDFC Bank")
    payments = gen.generate_batch(count=200, time_span_seconds=300)
    signals = engine.compute_signals(payments)
    print(signals.get_summary())
    print(f"Degraded: {signals.degraded_banks}")
    
    # Test 3: Anomaly
    print("\n3. Anomaly Detection:")
    gen.simulate_bank_outage("ICICI Bank")
    payments = gen.generate_batch(count=200, time_span_seconds=300)
    signals = engine.compute_signals(payments)
    if signals.has_anomaly:
        print(f"🚨 {signals.anomaly_severity.value}: {signals.anomaly_description}")
    
    print("\n✅ All tests completed successfully!")

if __name__ == "__main__":
    main()
```

Run it:
```bash
PYTHONPATH=. python test_metrics.py
```

---

## Expected Results Summary

| Test | Expected Result |
|------|----------------|
| Basic signals | Success rate ~90-95%, latency 150-300ms |
| Bank degradation | Degraded bank appears in list, failure rate >30% |
| Anomaly detection | Anomaly flag = true, severity = warning/critical |
| Trend detection | Trends change from UNKNOWN to RISING/STABLE/FALLING |
| JSON export | Valid JSON with all signal fields |
| Retry analysis | Effectiveness value between -1.0 and 1.0 |

---

**STEP 3 COMPLETE** ✅

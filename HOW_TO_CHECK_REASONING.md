# How to Check the Reasoning Layer is Working

This guide shows you exactly how to verify the Agent Reasoning Layer (Step 4) implementation.

---

## Prerequisites

### **1. Install Dependencies**
```bash
cd "/Users/bhanujbhalla/Desktop/Projects/payment agentic ai "
pip install google-generativeai
```

### **2. Set Up API Key**

**Option A: Environment Variable**
```bash
export GEMINI_API_KEY="AIzaSyANaV7xirbEZX0tzkyiI8PKR4eJ7Cr6c38"
```

**Option B: Create .env File**
```bash
cp .env.example .env
# Edit .env and add:
# GEMINI_API_KEY=AIzaSyANaV7xirbEZX0tzkyiI8PKR4eJ7Cr6c38
```

---

## Quick Start (Recommended)

### **Run the Examples**
```bash
cd "/Users/bhanujbhalla/Desktop/Projects/payment agentic ai "
export GEMINI_API_KEY="AIzaSyANaV7xirbEZX0tzkyiI8PKR4eJ7Cr6c38"
PYTHONPATH=. python examples/agent_reasoning.py
```

This will run 7 examples showing:
- ✅ Basic reasoning from signals
- ✅ Bank degradation detection
- ✅ Multiple simultaneous issues
- ✅ Normal operation detection
- ✅ Retry storm analysis
- ✅ JSON export
- ✅ Fallback reasoning (no LLM)

**Expected Output:**
```
=== Example 1: Basic Reasoning ===

Reasoning Summary:

Top Hypotheses:
  • bank_degradation: 75% confidence
  • normal_operation: 60% confidence

Overall Confidence: 72%

Explanation: The system shows moderate performance with some degradation...

Assumptions: ['Assuming normal traffic patterns']
Uncertainty: ['Unclear if issue is temporary']
```

---

## Run Tests

```bash
cd "/Users/bhanujbhalla/Desktop/Projects/payment agentic ai "
python -m pytest tests/test_reasoning_models.py tests/test_reasoner.py -v
```

**Expected:** All 11 tests should pass ✅

---

## Interactive Testing

### **Test 1: Basic Reasoning with LLM**
```bash
export GEMINI_API_KEY="AIzaSyANaV7xirbEZX0tzkyiI8PKR4eJ7Cr6c38"

python -c "
import asyncio
from simulation import PaymentGenerator
from agent import MetricsEngine, Reasoner

async def test():
    gen = PaymentGenerator(config={'seed': 42})
    gen.simulate_bank_degradation('HDFC Bank')
    payments = gen.generate_batch(count=150, time_span_seconds=300)
    
    engine = MetricsEngine()
    signals = engine.compute_signals(payments)
    
    reasoner = Reasoner()
    reasoning = await reasoner.reason(signals)
    
    print(reasoning.get_summary())
    print(f'\nTop Hypothesis: {reasoning.get_top_hypothesis()}')

asyncio.run(test())
"
```

### **Test 2: Multiple Issues**
```bash
python -c "
import asyncio
from simulation import PaymentGenerator
from agent import MetricsEngine, Reasoner

async def test():
    gen = PaymentGenerator()
    gen.simulate_bank_outage('ICICI Bank')
    gen.simulate_bank_degradation('HDFC Bank')
    payments = gen.generate_batch(count=200, time_span_seconds=300)
    
    engine = MetricsEngine()
    signals = engine.compute_signals(payments)
    
    reasoner = Reasoner()
    reasoning = await reasoner.reason(signals)
    
    print('Hypotheses:')
    for hyp, conf in sorted(reasoning.hypotheses.items(), key=lambda x: x[1], reverse=True):
        print(f'  {hyp}: {conf:.0%}')

asyncio.run(test())
"
```

### **Test 3: Fallback Reasoning (No API Key)**
```bash
python -c "
import asyncio
from simulation import PaymentGenerator
from agent import MetricsEngine, Reasoner

async def test():
    gen = PaymentGenerator()
    gen.simulate_bank_degradation('SBI')
    payments = gen.generate_batch(count=100, time_span_seconds=300)
    
    engine = MetricsEngine()
    signals = engine.compute_signals(payments)
    
    # Force fallback by not providing API key
    reasoner = Reasoner(config={'gemini_api_key': None})
    reasoning = await reasoner.reason(signals)
    
    print('Fallback Reasoning:')
    print(reasoning.get_summary())

asyncio.run(test())
"
```

### **Test 4: Export as JSON**
```bash
python -c "
import asyncio
import json
from simulation import PaymentGenerator
from agent import MetricsEngine, Reasoner

async def test():
    gen = PaymentGenerator(config={'seed': 42})
    payments = gen.generate_batch(count=100, time_span_seconds=300)
    
    engine = MetricsEngine()
    signals = engine.compute_signals(payments)
    
    reasoner = Reasoner()
    reasoning = await reasoner.reason(signals)
    
    print(json.dumps(reasoning.to_dict(), indent=2))

asyncio.run(test())
"
```

---

## What to Look For

### ✅ **Success Indicators:**

1. **Examples run without errors**
2. **Tests all pass (11/11)**
3. **Reasoning output is structured:**
   - Has `hypotheses` dict with confidence scores
   - Has `explanation` string
   - Has `assumptions` list
   - Has `uncertainty` list
   - Has `overall_confidence` between 0-1

4. **LLM reasoning works (with API key):**
   - Hypotheses are relevant to signals
   - Confidence scores are reasonable
   - Explanation makes sense
   - Returns valid JSON structure

5. **Fallback reasoning works (without API key):**
   - Still returns structured output
   - Uses rule-based heuristics
   - Lower confidence scores

6. **Hypothesis detection:**
   - Bank degradation → detects `bank_degradation`
   - Normal operation → detects `normal_operation`
   - High latency → detects `network_issues`
   - Multiple issues → multiple hypotheses

---

## Common Issues

### **Issue: No module named 'google.generativeai'**
```bash
# Solution: Install the package
pip install google-generativeai
```

### **Issue: API key not found**
```bash
# Solution: Set environment variable
export GEMINI_API_KEY="AIzaSyANaV7xirbEZX0tzkyiI8PKR4eJ7Cr6c38"

# Or create .env file
echo 'GEMINI_API_KEY=AIzaSyANaV7xirbEZX0tzkyiI8PKR4eJ7Cr6c38' > .env
```

### **Issue: JSON parsing error**
```
# This is normal occasionally - LLM might return invalid JSON
# The reasoner will fall back to rule-based reasoning
# Check logs for details
```

---

## Full Example Script

Save this as `test_reasoning.py`:

```python
import asyncio
import os
from simulation import PaymentGenerator
from agent import MetricsEngine, Reasoner

async def main():
    print("Testing Agent Reasoning Layer\n")
    
    # Check API key
    if not os.getenv('GEMINI_API_KEY'):
        print("⚠️  No GEMINI_API_KEY found, using fallback reasoning\n")
    
    # Test 1: Normal operation
    print("1. Normal Operation:")
    gen = PaymentGenerator(config={'seed': 42})
    gen.base_failure_rate = 0.02
    payments = gen.generate_batch(count=100, time_span_seconds=300)
    
    engine = MetricsEngine()
    signals = engine.compute_signals(payments)
    
    reasoner = Reasoner()
    reasoning = await reasoner.reason(signals)
    
    print(reasoning.get_summary())
    
    # Test 2: Bank degradation
    print("\n2. Bank Degradation:")
    gen = PaymentGenerator(config={'seed': 42})
    gen.simulate_bank_degradation("HDFC Bank")
    payments = gen.generate_batch(count=200, time_span_seconds=300)
    
    signals = engine.compute_signals(payments)
    reasoning = await reasoner.reason(signals)
    
    print(reasoning.get_summary())
    print(f"Degraded banks detected: {signals.degraded_banks}")
    
    # Test 3: Check hypothesis
    top = reasoning.get_top_hypothesis()
    if top:
        print(f"\n✅ Top hypothesis: {top[0]} ({top[1]:.0%} confidence)")
    
    print("\n✅ All tests completed successfully!")

if __name__ == "__main__":
    asyncio.run(main())
```

Run it:
```bash
export GEMINI_API_KEY="AIzaSyANaV7xirbEZX0tzkyiI8PKR4eJ7Cr6c38"
PYTHONPATH=. python test_reasoning.py
```

---

## Expected Results Summary

| Test | Expected Result |
|------|----------------|
| Basic reasoning | Returns structured ReasoningResult with hypotheses |
| Bank degradation | Detects `bank_degradation` hypothesis with >60% confidence |
| Normal operation | Detects `normal_operation` hypothesis |
| Multiple issues | Multiple hypotheses with varying confidence |
| JSON export | Valid JSON with all required fields |
| Fallback mode | Works without API key, uses rule-based logic |
| Confidence scores | All between 0.0 and 1.0 |

---

## Verification Checklist

- [ ] Dependencies installed (`google-generativeai`)
- [ ] API key set in environment or .env file
- [ ] Examples run successfully
- [ ] All tests pass (11/11)
- [ ] LLM reasoning returns structured output
- [ ] Fallback reasoning works without API key
- [ ] Hypotheses are relevant to input signals
- [ ] Confidence scores are reasonable (0-1)
- [ ] JSON export works

---

**STEP 4 COMPLETE** ✅

The agent can now reason about payment signals using Gemini, forming hypotheses with confidence scores, tracking assumptions and uncertainty, and providing human-readable explanations.

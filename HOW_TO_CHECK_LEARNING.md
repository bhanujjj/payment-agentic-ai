# How to Check Learning & Feedback Loop (Step 7)

## Quick Verification

### 1. Run Learning Demo
```bash
PYTHONPATH=. python examples/learning_demo.py
```

**Expected Output**:
```
ITERATION 1: FIRST ENCOUNTER (NO LEARNING YET)
  PRE-ACTION: 85.1% success, 711ms latency, 15 retries
  Action: recommend_retry_adjustment
  POST-ACTION: 98.5% success, 328ms latency, 0 retries
  Outcome: SUCCESS (score: 1.00)
  ✓ Stored in memory

ITERATION 2: SAME SCENARIO (LEARNING ACTIVE)
  Learning adjustment applied (if similar context)
  
LEARNING SUMMARY:
  recommend_retry_adjustment:
    - Observations: 1
    - Success Rate: 100%
    - Recommendation: RECOMMENDED (high success rate)
```

---

## What to Look For

### ✅ Learning Loop Components

1. **PRE-ACTION Metrics Captured**
   - Success rate
   - Latency
   - Retry count
   - Error rate

2. **Action Executed**
   - State change applied
   - Configuration updated

3. **POST-ACTION Metrics Captured**
   - Same metrics after action
   - From new simulated payments

4. **Impact Computed**
   ```
   Success Rate: 85.1% → 98.5% (Δ +13.4%)
   Latency: 711ms → 328ms (Δ -383ms)
   Retries: 15 → 0 (Δ -15)
   ```

5. **Outcome Evaluated**
   ```
   Outcome: SUCCESS (score: 1.00)
   ```

6. **Memory Stored**
   ```
   ✓ Stored: recommend_retry_adjustment → SUCCESS
     Context: moderate success, degraded banks, ineffective retries
   ```

7. **Future Decisions Influenced**
   - Learning adjustment applied in iteration 2
   - Action scores boosted/penalized based on past outcomes

---

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│ COMPLETE AGENTIC LOOP                                   │
│ ─────────────────────────────────────────────────────   │
│                                                          │
│ 1. Observe (Signals)                                    │
│ 2. Reason (Hypotheses)                                  │
│ 3. Decide (Action Selection)                            │
│ 4. Execute (State Change)                               │
│ 5. Measure (Post-Action Metrics)                        │
│ 6. Evaluate (Outcome Classification)                    │
│ 7. Learn (Memory + Weight Adjustment)                   │
│ 8. Repeat (Improved Decisions)                          │
│                                                          │
└─────────────────────────────────────────────────────────┘
```

---

## Components

### 1. Learning Models (`agent/learning_models.py`)
- `ActionOutcome`: Records action results with metrics
- `OutcomeClassification`: SUCCESS/NEUTRAL/FAILURE
- `LearningStats`: Aggregated statistics

### 2. Memory Storage (`agent/memory.py`)
- JSON-based persistence
- Similarity search for context matching
- Action statistics tracking

### 3. Outcome Evaluator (`agent/evaluator.py`)
- Deterministic evaluation rules
- Scores based on metric deltas
- Classification thresholds

### 4. Action Learner (`agent/learner.py`)
- Weight adjustment (0.8x to 1.2x)
- Based on past success/failure rates
- Bounded and explainable

### 5. Decision Engine Integration
- Learner integrated into `DecisionEngine`
- Automatic score adjustment
- Logged for transparency

---

## Example Outcome Record

```json
{
  "context_summary": "moderate success, SBI degraded, retry storm",
  "action": "recommend_retry_adjustment",
  "risk_level": "LOW",
  "pre_success_rate": 0.851,
  "post_success_rate": 0.985,
  "success_rate_delta": 0.134,
  "latency_delta": -383,
  "retry_delta": -15,
  "outcome": "SUCCESS",
  "outcome_score": 1.0,
  "timestamp": "2026-02-01T05:58:51.407000"
}
```

---

## Learning in Action

### Scenario 1: First Encounter
```
No learning data available
→ Uses base scoring only
→ Action selected: recommend_retry_adjustment
→ Outcome: SUCCESS (+13.4% success rate)
→ Stored in memory
```

### Scenario 2: Same Context
```
Learning data available (1 SUCCESS)
→ Context matches: "moderate success, retry storm"
→ Learning adjustment: 1.15x boost
→ Action score: 0.75 → 0.86
→ More likely to select same action
```

### Scenario 3: After Failure
```
Learning data: 2 FAILURES, 1 SUCCESS
→ Failure rate: 67%
→ Learning adjustment: 0.85x penalty
→ Action score: 0.75 → 0.64
→ Less likely to select this action
```

---

## Verification Checklist

- [ ] Memory file created: `./data/memory/learning_demo.json`
- [ ] Outcome stored with all metrics
- [ ] Evaluation shows SUCCESS/NEUTRAL/FAILURE
- [ ] Learning summary shows action stats
- [ ] Future decisions show adjustment logs
- [ ] Adjustments are bounded (0.8x to 1.2x)
- [ ] No LLMs used in learning logic

---

## Key Metrics

### Outcome Evaluation Thresholds
- **SUCCESS**: score ≥ 0.7
  - Success rate improved >5%
  - Latency reduced >100ms
  - Retries reduced >10

- **NEUTRAL**: 0.3 < score < 0.7
  - Mixed or minimal changes

- **FAILURE**: score ≤ 0.3
  - Success rate degraded >5%
  - Latency increased >100ms
  - Retries increased >10

### Learning Adjustments
- **Boost**: 1.0 to 1.2x (max 20% boost)
  - When success rate >60% in similar contexts
  
- **Penalty**: 0.8 to 1.0x (max 20% penalty)
  - When failure rate >60% in similar contexts

- **Neutral**: 1.0x
  - Mixed results or insufficient data (<2 samples)

---

## Memory Location

Default: `./data/memory/action_memory.json`

**Format**:
```json
{
  "version": "1.0",
  "saved_at": "ISO-8601",
  "memories": [...]
}
```

**Clear Memory**:
```python
from agent.memory import ActionMemory
memory = ActionMemory()
memory.clear()
```

---

## Testing

```bash
# Run learning demo
PYTHONPATH=. python examples/learning_demo.py

# Check memory file
cat ./data/memory/learning_demo.json

# Verify learning stats
python -c "
from agent.memory import ActionMemory
memory = ActionMemory('./data/memory/learning_demo.json')
print(memory.get_summary())
"
```

---

## Success Criteria

✅ **All Met**:
1. Memory stores action outcomes
2. Outcome evaluation is deterministic
3. Learning adjusts future decisions
4. Demo shows before/after metrics
5. Demo shows memory being used
6. Full agentic loop is closed
7. No LLMs in learning logic
8. Adjustments are bounded and explainable

---

## STEP 7 COMPLETE ✅

The agent now has a complete learning loop:
- Observes outcomes
- Evaluates success/failure
- Stores experience
- Improves future decisions

**Next**: Production deployment (Step 8)

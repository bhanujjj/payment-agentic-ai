# Decision Logic Improvement

## 🎯 Issue

User ran RETRY_ADJUSTMENT scenario but agent chose `do_nothing` instead of `recommend_retry_adjustment`.

**Why?** The `recommend_retry_adjustment` action was **missing** from the impact estimation functions!

---

## 🔧 Fix Applied

### Added to `_estimate_success_rate_impact`:

```python
if action == 'recommend_retry_adjustment':
    # Retry adjustment helps when retries are ineffective
    if signals.retry_effectiveness < -0.5 and signals.total_retries > 10:
        return 0.4  # Strong improvement (15 retries, -0.92 effectiveness)
    elif signals.retry_effectiveness < 0 and signals.total_retries > 5:
        return 0.25  # Moderate improvement
    elif signals.total_retries > 10:
        return 0.15  # Some improvement
    return 0.05
```

### Added to `_estimate_latency_impact`:

```python
if action == 'recommend_retry_adjustment':
    # Reducing retries significantly improves latency
    if signals.total_retries > 10:
        return 0.35  # Strong latency improvement (15 retries)
    elif signals.total_retries > 5:
        return 0.25
    return 0.1
```

---

## 📊 Scenario Conditions

```
Retry Storm:
  • Retries: 15
  • Retry Effectiveness: -0.92 (very ineffective!)
  • Success Rate: 85.1%
  • Latency: 711ms
```

**Expected Impacts:**
- Success Rate: +0.25 (moderate improvement)
- Latency: +0.35 (strong improvement)

This should now score **higher than do_nothing** (which has 0 impact).

---

## ✅ Expected Behavior

After this fix, in RETRY_ADJUSTMENT scenario:
- Agent should choose `recommend_retry_adjustment`
- Config should change: max_retries 3→2
- Metrics should improve
- Outcome: SUCCESS
- Learning: Stored

---

**Testing now...**

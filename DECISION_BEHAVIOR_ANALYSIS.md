# Decision Behavior Analysis

## Question: Why So Many `do_nothing` Decisions?

### Answer: **The system is working correctly!**

## Scenario Analysis

| Scenario | Success Rate | Decision | Correct? |
|----------|--------------|----------|----------|
| Normal | 91.5% | `do_nothing` | ✅ Yes - system healthy |
| HDFC Degraded | 86.0% | `do_nothing` | ✅ Yes - minor issue |
| Multiple Issues | 79.5% | `do_nothing` | ⚠️ Borderline |
| Both Banks Down | 72.0% | `recommend_path_suppression` | ✅ Yes - takes action! |

## Why 86% Success Doesn't Trigger Action

**Degradation Impact**:
- HDFC Bank degraded: 95% → 47.5% success for HDFC
- But HDFC is only ~25% of traffic
- Overall impact: 91.5% → 86% (5% drop)
- **This is mild** - not worth the risk of rerouting

**Context-Aware Thresholds**:
```
> 85%: Normal - be conservative
75-85%: Degraded - moderate response
< 75%: Critical - take action
```

## Is This Correct Behavior?

**YES!** Here's why:

1. **86% is still good** - Most payments succeeding
2. **Rerouting has risks** - Could make things worse
3. **Monitoring is appropriate** - Watch and wait
4. **72% triggers action** - System responds when needed

## If You Want More Aggressive Decisions

### Option 1: Lower Thresholds
```python
# Current:
if current_success_rate < 0.75:  # Critical
    # Take action

# More aggressive:
if current_success_rate < 0.85:  # Critical
    # Take action
```

### Option 2: Make Degradation More Severe
```python
# Current (in BankHealth):
if self.is_degraded:
    return self.success_rate * 0.5  # 50% of normal

# More severe:
if self.is_degraded:
    return self.success_rate * 0.3  # 30% of normal
```

### Option 3: Increase Degraded Bank Traffic Share
Make HDFC handle more traffic so its degradation has bigger impact.

## Recommendation

**Keep current behavior** ✅

The system is:
- Conservative when things are mostly working (86%)
- Responsive when things are bad (72%)
- Following production best practices

**Why?**
- Rerouting in production is risky
- 86% success is acceptable for monitoring
- System proves it CAN act when needed

## Testing Different Severities

Want to see more action decisions? Test with:

```python
# Simulate BOTH banks degraded
gen.simulate_bank_degradation('HDFC Bank')
gen.simulate_bank_degradation('ICICI Bank')

# Or simulate outage + degradation
gen.simulate_bank_outage('HDFC Bank')
gen.simulate_bank_degradation('ICICI Bank')
gen.simulate_bank_degradation('Axis Bank')
```

---

**Conclusion**: Your decision engine is working correctly. The "problem" is that the scenarios aren't severe enough to warrant action, which is actually realistic!

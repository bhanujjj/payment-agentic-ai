# Decision Scoring - Context-Aware Fix

## Problem

All decisions were `do_nothing` even in severe scenarios (72% success rate with 2 banks down).

## Root Cause

The scoring formula **over-penalized risk**:

```python
# Old scoring:
if risk_level == RiskLevel.MEDIUM:
    score *= 0.8  # 20% penalty!
```

This meant high-impact actions like `recommend_reroute` (+30% success improvement) scored **lower** than `do_nothing` because of the risk penalty.

## Solution

Made scoring **context-aware** based on current success rate:

### When Success Rate < 75% (Critical)
- **Boost success impact weight**: 0.6 (from 0.4)
- **Reduce risk penalties**:
  - MEDIUM risk: 0.95x (was 0.8x)
  - HIGH risk: 0.8x (was 0.6x)
- **Message**: "We're in trouble, take action!"

### When Success Rate < 85% (Degraded)
- **Moderate success weight**: 0.5
- **Moderate risk penalties**:
  - MEDIUM risk: 0.9x
  - HIGH risk: 0.7x
- **Message**: "Be cautious but willing to act"

### When Success Rate >= 85% (Normal)
- **Conservative weights**: 0.4
- **Strict risk penalties**:
  - MEDIUM risk: 0.85x
  - HIGH risk: 0.6x
- **Message**: "Don't fix what isn't broken"

## Results

### Before (Broken)
```
Scenario: 72% success, 2 banks down
Decision: do_nothing (77%)
  - do_nothing: 77%
  - recommend_reroute: 61% ← Should win!
```

### After (Fixed)
```
Scenario: 72% success, 2 banks down
Decision: recommend_path_suppression (72%)
  - recommend_path_suppression: 72% ← WINS!
  - recommend_reroute: 70%
  - do_nothing: 69% ← Now lower
```

## Code Changes

### File: `agent/decider.py`

**Modified**: `_calculate_final_score()`
- Added `signals: PaymentSignals` parameter
- Context-aware weight calculation
- Context-aware risk penalties

**Modified**: `_score_action()`
- Pass `signals` to `_calculate_final_score()`

## Behavior Summary

| Success Rate | Scenario | Decision Behavior |
|--------------|----------|-------------------|
| < 75% | Critical | Aggressive - take action to recover |
| 75-85% | Degraded | Moderate - willing to intervene |
| > 85% | Normal | Conservative - monitor only |

## Testing

```bash
PYTHONPATH=. python test_decision_scoring.py
```

**Results**:
- ✅ Critical scenarios now trigger actions
- ✅ Normal scenarios remain conservative
- ✅ Degraded scenarios are balanced

---

**Status**: ✅ Fixed  
**Date**: 2026-02-01  
**Impact**: System now makes appropriate decisions based on severity

# How Hypotheses and Scores are Generated

## 🎯 **Answer: Two-Stage Process**

The hypotheses and scores come from **TWO sources**:

1. **Deterministic Rules** (Primary) - Rule-based scoring
2. **Gemini AI Model** (Secondary) - Human-readable explanation only

---

## 📊 **Stage 1: Deterministic Reasoning (The Scores)**

### **Location:** [`agent/reasoner.py`](file:///Users/bhanujbhalla/Desktop/Projects/payment%20agentic%20ai%20/agent/reasoner.py) - `_deterministic_reasoning()`

This is where **ALL the hypothesis scores come from**. The AI model does NOT generate these scores!

### **How It Works:**

```python
def _deterministic_reasoning(self, signals: PaymentSignals) -> ReasoningResult:
    """Rule-based reasoning - NO AI MODEL INVOLVED"""
    
    hypotheses = {}  # Empty dict to store hypothesis scores
    assumptions = []
    uncertainty = []
    explanation_parts = []
    
    # RULE 1: Check for normal operation
    if signals.overall_success_rate > 0.95 and not signals.has_anomaly:
        hypotheses["normal_operation"] = 0.9  # 90% confidence
        explanation_parts.append("System appears to be operating normally.")
    
    # RULE 2: Check for bank degradation
    if signals.degraded_banks:
        hypotheses["bank_degradation"] = 0.8  # 80% confidence
        explanation_parts.append(f"Detected degraded banks: {', '.join(signals.degraded_banks)}.")
        assumptions.append("Bank degradation is the primary cause")
    
    # RULE 3: Check for bank outage
    if signals.overall_failure_rate > 0.5:
        hypotheses["bank_outage"] = 0.7  # 70% confidence
        explanation_parts.append("Very high failure rate suggests possible outage.")
    
    # RULE 4: Check for network issues
    if signals.p95_latency_ms > 1000:
        hypotheses["network_issues"] = 0.6  # 60% confidence
        explanation_parts.append("High latency detected.")
    
    # RULE 5: Check for retry storm
    if signals.total_retries > signals.total_payments * 0.3:
        hypotheses["retry_storm"] = 0.65  # 65% confidence
        explanation_parts.append("High retry rate detected.")
    
    # RULE 6: Check retry effectiveness
    if signals.retry_effectiveness < -0.2:
        uncertainty.append("Retries don't seem to be helping")
    
    # RULE 7: Check for peak load
    if signals.total_payments > 1000:
        hypotheses["peak_load"] = 0.5  # 50% confidence
        explanation_parts.append("High payment volume detected.")
    
    # Calculate overall confidence (average of hypothesis scores)
    overall_confidence = sum(hypotheses.values()) / len(hypotheses) if hypotheses else 0.5
    
    # Create explanation from parts
    explanation = " ".join(explanation_parts) if explanation_parts else "No clear issues detected."
    
    return ReasoningResult(
        hypotheses=hypotheses,
        overall_confidence=overall_confidence,
        assumptions=assumptions,
        uncertainty=uncertainty,
        explanation=explanation
    )
```

### **Example Output:**

```python
# Input signals:
signals.degraded_banks = ['State Bank of India', 'Yes Bank']
signals.total_retries = 15
signals.total_payments = 215
signals.retry_effectiveness = -0.92

# Deterministic reasoning produces:
hypotheses = {
    "bank_degradation": 0.8,      # Rule 2 triggered
    "retry_storm": 0.65           # Rule 5 triggered (15 > 215 * 0.3)
}
overall_confidence = (0.8 + 0.65) / 2 = 0.725
assumptions = ["Bank degradation is the primary cause"]
uncertainty = ["Retries don't seem to be helping"]  # Rule 6 triggered
explanation = "Detected degraded banks: State Bank of India, Yes Bank. High retry rate detected."
```

---

## 🤖 **Stage 2: Gemini AI Model (The Explanation)**

### **Location:** [`agent/reasoner.py`](file:///Users/bhanujbhalla/Desktop/Projects/payment%20agentic%20ai%20/agent/reasoner.py) - `_get_llm_explanation()`

The AI model **ONLY** generates a human-readable explanation. It does **NOT** generate the hypothesis scores!

### **How It Works:**

```python
async def _get_llm_explanation(self, signals: PaymentSignals, reasoning: ReasoningResult) -> str:
    """Get human-readable explanation from Gemini AI"""
    
    # Build prompt with signals and deterministic reasoning
    prompt = f"""You are analyzing a payment system.

Payment Signals:
- Success Rate: {signals.overall_success_rate:.1%}
- Failure Rate: {signals.overall_failure_rate:.1%}
- Latency: {signals.avg_latency_ms:.0f}ms
- Retries: {signals.total_retries}
- Retry Effectiveness: {signals.retry_effectiveness:.2f}
- Degraded Banks: {', '.join(signals.degraded_banks) if signals.degraded_banks else 'None'}

Detected Issues:
{reasoning.explanation}

Provide a brief (1-2 sentences) explanation of what's happening.
"""
    
    # Call Gemini API
    response = await self.llm_client.generate_content_async(
        prompt,
        generation_config={
            'temperature': self.temperature,
            'max_output_tokens': 200
        }
    )
    
    # Return AI-generated explanation
    return response.text.strip()
```

### **Example Output:**

```
"Detected bank degradation (State Bank of India, Yes Bank) causing elevated 
failure rates. High retry count suggests ineffective retry strategy."
```

---

## 🔄 **Complete Flow**

```mermaid
flowchart TD
    Start([Payment Signals]) --> Deterministic[_deterministic_reasoning]
    
    Deterministic --> Rules{Apply Rules}
    
    Rules -->|Success > 95%| Normal[hypotheses['normal_operation'] = 0.9]
    Rules -->|Degraded Banks| BankDeg[hypotheses['bank_degradation'] = 0.8]
    Rules -->|Failure > 50%| Outage[hypotheses['bank_outage'] = 0.7]
    Rules -->|Latency > 1000ms| Network[hypotheses['network_issues'] = 0.6]
    Rules -->|Retries > 30%| Storm[hypotheses['retry_storm'] = 0.65]
    
    Normal --> Combine[Combine All Hypotheses]
    BankDeg --> Combine
    Outage --> Combine
    Network --> Combine
    Storm --> Combine
    
    Combine --> CalcConf[Calculate Overall Confidence<br/>Average of all scores]
    
    CalcConf --> Result1[ReasoningResult with scores]
    
    Result1 --> TryAI{Gemini API<br/>Available?}
    
    TryAI -->|Yes| CallGemini[_get_llm_explanation]
    TryAI -->|No| UseDefault[Use default explanation]
    
    CallGemini --> AIExplanation[AI-generated explanation]
    UseDefault --> DefaultExplanation[Rule-based explanation]
    
    AIExplanation --> FinalResult[Final ReasoningResult]
    DefaultExplanation --> FinalResult
    
    FinalResult --> End([Return to Decision Engine])
    
    style Deterministic fill:#fff3cd
    style Rules fill:#e3f2fd
    style Combine fill:#f3e5f5
    style CallGemini fill:#e8f5e9
    style FinalResult fill:#d4edda
```

---

## 📝 **Key Points**

### ✅ **Hypothesis Scores = Deterministic Rules**
- **NOT** generated by AI model
- **Hard-coded** confidence values (0.5 to 0.9)
- Based on **signal thresholds**
- **Predictable and testable**

### ✅ **AI Model = Explanation Only**
- **ONLY** generates human-readable text
- **Does NOT** affect hypothesis scores
- **Optional** - system works without it
- **Enhances** user understanding

### ✅ **Why This Design?**
1. **Reliability** - Deterministic scoring is predictable
2. **Testability** - Easy to unit test rules
3. **Speed** - No AI latency for critical decisions
4. **Transparency** - Clear why each hypothesis scored what it did
5. **Fallback** - Works even if AI API fails

---

## 🎯 **Example Breakdown**

### **Your Demo Output:**
```
Hypotheses Generated:
  • bank_degradation: 80% confidence
```

### **How This Was Generated:**

1. **Deterministic Rule Triggered:**
   ```python
   if signals.degraded_banks:  # ['State Bank of India', 'Yes Bank']
       hypotheses["bank_degradation"] = 0.8  # ← This is the 80%!
   ```

2. **Gemini AI Generated:**
   ```
   "Detected bank degradation (8..."  # Just the explanation text
   ```

---

## 📊 **All Hypothesis Rules**

| Hypothesis | Trigger Condition | Confidence Score |
|------------|------------------|------------------|
| `normal_operation` | Success > 95% AND no anomaly | 0.9 (90%) |
| `bank_degradation` | Degraded banks detected | 0.8 (80%) |
| `bank_outage` | Failure rate > 50% | 0.7 (70%) |
| `retry_storm` | Retries > 30% of payments | 0.65 (65%) |
| `network_issues` | P95 latency > 1000ms | 0.6 (60%) |
| `peak_load` | Total payments > 1000 | 0.5 (50%) |

**Overall Confidence** = Average of all triggered hypothesis scores

---

**The AI model is just for pretty explanations - all the real reasoning is deterministic!** 🎯

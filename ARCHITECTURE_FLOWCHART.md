# Payment Routing Agent - Complete Architecture

## 🎯 System Overview

```mermaid
graph TB
    Start([User Starts Demo]) --> ScenarioSelect{Select Scenario}
    
    ScenarioSelect -->|1| Autonomous[Autonomous Mode<br/>Mixed Conditions]
    ScenarioSelect -->|2| RetryStorm[Retry Adjustment<br/>High Retry Rate]
    ScenarioSelect -->|3| DoNothing[Do-Nothing<br/>Healthy System]
    
    Autonomous --> Init[Initialize Components]
    RetryStorm --> Init
    DoNothing --> Init
    
    Init --> PaymentGen[Payment Generator<br/>Simulate Traffic]
    
    PaymentGen --> Metrics[Metrics Engine<br/>Compute Signals]
    
    Metrics --> Reasoning[AI Reasoner<br/>Gemini 2.5 Flash]
    
    Reasoning --> Decision[Decision Engine<br/>Score Actions]
    
    Decision --> Execute{Execute Action}
    
    Execute -->|do_nothing| NoChange[No Config Change]
    Execute -->|recommend_retry_adjustment| ChangeConfig[Update max_retries<br/>3 → 2]
    Execute -->|Other Actions| OtherChange[Other Config Changes]
    
    NoChange --> Measure{Measure Impact}
    ChangeConfig --> Measure
    OtherChange --> Measure
    
    Measure -->|Intervention| NewTraffic[Generate New Traffic<br/>Measure Real Impact]
    Measure -->|Non-Intervention| SameTraffic[Use Same Traffic<br/>Show No Change]
    
    NewTraffic --> Evaluate[Outcome Evaluator]
    SameTraffic --> Evaluate
    
    Evaluate -->|Intervention| ClassifyIntervention{Classify Outcome}
    Evaluate -->|Non-Intervention| Neutral[NEUTRAL<br/>No Attribution]
    
    ClassifyIntervention -->|Metrics Improved| Success[SUCCESS]
    ClassifyIntervention -->|Metrics Degraded| Failure[FAILURE]
    ClassifyIntervention -->|No Change| NeutralInt[NEUTRAL]
    
    Success --> StoreMemory[Store in Memory<br/>Learn from Outcome]
    Failure --> StoreMemory
    NeutralInt --> StoreMemory
    Neutral --> SkipMemory[Skip Memory<br/>Causality-Safe]
    
    StoreMemory --> Learning[Action Learner<br/>Update Weights]
    SkipMemory --> Summary[Final Summary]
    
    Learning --> Summary
    
    Summary --> End([Demo Complete])
    
    style Start fill:#e1f5e1
    style End fill:#e1f5e1
    style Reasoning fill:#fff3cd
    style Decision fill:#fff3cd
    style Success fill:#d4edda
    style Failure fill:#f8d7da
    style Neutral fill:#d1ecf1
    style SkipMemory fill:#d1ecf1
```

---

## 🔄 Detailed Component Flow

```mermaid
flowchart LR
    subgraph Input["📥 INPUT LAYER"]
        PG[Payment Generator]
        Traffic[Payment Traffic]
    end
    
    subgraph Observe["👁️ OBSERVATION LAYER"]
        ME[Metrics Engine]
        Signals[Payment Signals]
    end
    
    subgraph Reason["🧠 REASONING LAYER"]
        AIR[AI Reasoner<br/>Gemini]
        Hypotheses[Hypotheses]
    end
    
    subgraph Decide["⚖️ DECISION LAYER"]
        DE[Decision Engine]
        Candidates[Candidate Actions]
        Scoring[Action Scoring]
        Selection[Best Action]
    end
    
    subgraph Execute["⚡ EXECUTION LAYER"]
        AE[Action Executor]
        Config[Runtime Config]
    end
    
    subgraph Measure["📊 MEASUREMENT LAYER"]
        PostTraffic[Post-Action Traffic]
        PostMetrics[Post-Action Metrics]
    end
    
    subgraph Evaluate["✅ EVALUATION LAYER"]
        OE[Outcome Evaluator]
        Classification[Outcome Classification]
    end
    
    subgraph Learn["🎓 LEARNING LAYER"]
        Memory[Action Memory]
        Learner[Action Learner]
        Weights[Action Weights]
    end
    
    PG --> Traffic
    Traffic --> ME
    ME --> Signals
    Signals --> AIR
    AIR --> Hypotheses
    Hypotheses --> DE
    DE --> Candidates
    Candidates --> Scoring
    Scoring --> Selection
    Selection --> AE
    AE --> Config
    Config --> PostTraffic
    PostTraffic --> PostMetrics
    PostMetrics --> OE
    OE --> Classification
    Classification --> Memory
    Memory --> Learner
    Learner --> Weights
    Weights -.Feedback.-> DE
    
    style Input fill:#e3f2fd
    style Observe fill:#fff3e0
    style Reason fill:#f3e5f5
    style Decide fill:#e8f5e9
    style Execute fill:#fce4ec
    style Measure fill:#e0f2f1
    style Evaluate fill:#fff9c4
    style Learn fill:#f1f8e9
```

---

## 🔍 Decision Engine Detail

```mermaid
flowchart TD
    Start([Reasoning Result + Signals]) --> GenCandidates[Generate Candidate Actions]
    
    GenCandidates --> CheckRetries{Retries > 5<br/>OR<br/>Effectiveness < 0?}
    
    CheckRetries -->|Yes| AddRetryAdj[Add recommend_retry_adjustment]
    CheckRetries -->|No| CheckHypothesis{Check Hypotheses}
    
    AddRetryAdj --> CheckHypothesis
    
    CheckHypothesis -->|bank_degradation| AddReroute[Add recommend_reroute]
    CheckHypothesis -->|retry_storm| AddRetryRed[Add recommend_retry_reduction]
    CheckHypothesis -->|network_issues| AddCircuit[Add circuit_breaker]
    
    AddReroute --> ScoreAll[Score All Actions]
    AddRetryRed --> ScoreAll
    AddCircuit --> ScoreAll
    
    ScoreAll --> CalcImpact[Calculate Impact Scores]
    
    CalcImpact --> SuccessImpact[Success Rate Impact<br/>-1 to +1]
    CalcImpact --> LatencyImpact[Latency Impact<br/>-1 to +1]
    CalcImpact --> CostImpact[Cost Impact<br/>0 to 1]
    
    SuccessImpact --> FinalScore[Calculate Final Score]
    LatencyImpact --> FinalScore
    CostImpact --> FinalScore
    
    FinalScore --> ApplyWeights[Apply Learning Weights]
    
    ApplyWeights --> SelectBest[Select Highest Scoring Action]
    
    SelectBest --> Decision([Decision Object])
    
    style Start fill:#e1f5e1
    style Decision fill:#e1f5e1
    style AddRetryAdj fill:#fff3cd
    style CalcImpact fill:#d1ecf1
    style SelectBest fill:#d4edda
```

---

## ⚖️ Causality-Safe Learning

```mermaid
flowchart TD
    Action{Action Type?}
    
    Action -->|do_nothing<br/>alert_ops| NonIntervention[Non-Intervention]
    Action -->|recommend_retry_adjustment<br/>recommend_reroute<br/>etc.| Intervention[Intervention]
    
    NonIntervention --> SameTraffic[Use Same Traffic<br/>for Comparison]
    Intervention --> NewTraffic[Generate New Traffic<br/>with Updated Config]
    
    SameTraffic --> NoChange[Metrics Unchanged]
    NewTraffic --> MeasureChange[Measure Metric Changes]
    
    NoChange --> NeutralOutcome[Outcome: NEUTRAL<br/>Score: 0.5]
    MeasureChange --> EvaluateMetrics{Metrics<br/>Improved?}
    
    EvaluateMetrics -->|Yes| SuccessOutcome[Outcome: SUCCESS<br/>Score: 0.7-1.0]
    EvaluateMetrics -->|No| FailureOutcome[Outcome: FAILURE<br/>Score: 0.0-0.3]
    EvaluateMetrics -->|Unchanged| NeutralOutcome2[Outcome: NEUTRAL<br/>Score: 0.3-0.7]
    
    NeutralOutcome --> SkipLearning[Skip Learning<br/>No Memory Storage]
    SuccessOutcome --> StoreLearning[Store in Memory<br/>Update Weights]
    FailureOutcome --> StoreLearning
    NeutralOutcome2 --> StoreLearning
    
    SkipLearning --> Reason1[Reason: No intervention<br/>No causality]
    StoreLearning --> Reason2[Reason: Agent intervened<br/>Can attribute outcome]
    
    Reason1 --> End([Causality-Safe])
    Reason2 --> End
    
    style NonIntervention fill:#d1ecf1
    style Intervention fill:#fff3cd
    style NeutralOutcome fill:#d1ecf1
    style SuccessOutcome fill:#d4edda
    style FailureOutcome fill:#f8d7da
    style SkipLearning fill:#d1ecf1
    style StoreLearning fill:#d4edda
```

---

## 📁 Project Structure

```mermaid
graph TB
    Root[payment agentic ai/]
    
    Root --> Agent[agent/]
    Root --> Data[data/]
    Root --> Examples[examples/]
    Root --> Demo[FULL_DEMO.py]
    
    Agent --> Generator[generator.py<br/>Payment Simulation]
    Agent --> Signals[signals.py<br/>Metrics Engine]
    Agent --> Reasoner[reasoner.py<br/>AI Reasoning]
    Agent --> Decider[decider.py<br/>Decision Engine]
    Agent --> Executor[executor.py<br/>Action Execution]
    Agent --> Evaluator[evaluator.py<br/>Outcome Evaluation]
    Agent --> Memory[memory.py<br/>Action Memory]
    Agent --> Learner[learner.py<br/>Action Learning]
    
    Data --> Schemas[schemas/]
    Data --> MemoryFiles[memory/]
    
    Examples --> ReasoningEx[agent_reasoning.py]
    Examples --> DecisionEx[decision_making.py]
    Examples --> ConfigEx[runtime_config_demo.py]
    
    style Root fill:#e3f2fd
    style Agent fill:#fff3e0
    style Data fill:#f3e5f5
    style Examples fill:#e8f5e9
    style Demo fill:#fce4ec
```

---

## 🎯 Key Features

### ✅ Honest Agent Behavior
- No forced actions
- No decision overrides
- Scenario controls only initial conditions
- Agent logic remains autonomous

### ✅ Causality-Safe Learning
- Non-intervention actions → NEUTRAL outcome
- No false attribution of metric changes
- Learning only from actual interventions
- Natural variance not credited to agent

### ✅ Realistic Simulation
- Proportional impact modeling
- Config change 3→2 = 33% retry reduction
- Believable metric improvements
- No miraculous changes

---

**Complete autonomous agent with full observability and learning!** 🎉

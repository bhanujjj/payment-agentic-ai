# 🚀 Payment Routing Agent

## Complete Autonomous Payment System

A production-grade autonomous agent that monitors payment system health, detects issues using AI, makes intelligent decisions, executes safe actions, and learns from outcomes.

---

## 🎯 Quick Demo (For Judges)

### Run the Complete Interactive Demo

```bash
PYTHONPATH=. python FULL_DEMO.py
```

**What it shows**:
- ✅ Payment simulation with retry storm
- ✅ AI-powered reasoning (Gemini 2.5 Flash)
- ✅ Intelligent decision making
- ✅ Runtime configuration changes
- ✅ Impact measurement (+13% success rate improvement)
- ✅ Learning from outcomes

**Duration**: ~5 minutes (interactive, press ENTER to advance)

---

## 📊 System Architecture

```
Observe → Reason → Decide → Execute → Measure → Evaluate → Learn → Improve
   ↑                                                                    ↓
   └────────────────────────────────────────────────────────────────────┘
                        Complete Agentic Loop
```

### Components

1. **Simulation Layer** - Realistic payment data generation
2. **Metrics Engine** - Real-time performance monitoring
3. **AI Reasoning** - Gemini 2.5 Flash for hypothesis generation
4. **Decision Engine** - Context-aware action selection
5. **Action Executor** - Safe runtime configuration changes
6. **Outcome Evaluator** - Success/failure classification
7. **Learning System** - Memory-based decision improvement

---

## 🚀 Getting Started

### Prerequisites

```bash
pip install -r requirements.txt
```

### Environment Setup

Create `.env` file:
```env
GEMINI_API_KEY=your_api_key_here
GEMINI_MODEL=gemini-2.5-flash
```

**Note**: System works without API key (uses deterministic fallback)

---

## 📁 Project Structure

```
payment-agentic-ai/
├── FULL_DEMO.py              # Complete demo script
├── README_DEMO.md            # Detailed demo guide
├── agent/                    # Core agent components
│   ├── metrics.py
│   ├── reasoner.py
│   ├── decider.py
│   ├── executor.py
│   ├── evaluator.py
│   ├── learner.py
│   └── memory.py
├── simulation/               # Payment simulation
├── examples/                 # Individual demos
├── tests/                    # Unit tests (18+)
└── docs/                     # Documentation
```

---

## 🎬 Demo Scenarios

### 1. Complete System Demo
```bash
PYTHONPATH=. python FULL_DEMO.py
```
Shows entire agentic loop with learning

### 2. Learning Loop Only
```bash
PYTHONPATH=. python examples/learning_demo.py
```
Focuses on outcome evaluation and memory

### 3. Runtime Config Change
```bash
PYTHONPATH=. python examples/runtime_config_demo.py
```
Shows safe configuration updates

---

## 🧪 Testing

```bash
# Run all tests
pytest tests/ -v

# Run specific component tests
pytest tests/test_executor.py -v
pytest tests/test_decider.py -v
```

**Test Coverage**: 18+ tests, all passing ✅

---

## 📈 Key Results

### Performance Improvement
- **Success Rate**: 85.1% → 98.5% (+13.4%)
- **Latency**: 711ms → 328ms (-383ms)
- **Retries**: 15 → 0 (-15 retries)
- **Outcome**: SUCCESS (score: 1.00)

### Learning Evidence
- Memory stored: `./data/memory/full_demo.json`
- Action success rate tracked: 100%
- Future decisions adjusted based on outcomes

---

## 🔑 Key Features

### 1. Autonomous Operation
- Self-monitoring and self-healing
- No human intervention required
- Continuous learning and improvement

### 2. AI-Powered Reasoning
- Gemini 2.5 Flash integration
- Hypothesis generation
- Natural language explanations
- **Works without LLM** (deterministic fallback)

### 3. Safe Action Execution
- Approval guardrails for high-risk actions
- Runtime config changes (no code modification)
- Reversible actions with state tracking
- Comprehensive logging

### 4. Learning from Experience
- Stores outcomes in persistent memory
- Evaluates success/failure deterministically
- Adjusts future decisions (0.8x to 1.2x)
- Bounded and explainable

---

## 🛠️ Technical Stack

- **Language**: Python 3.12
- **AI**: Google Gemini 2.5 Flash
- **Storage**: JSON-based memory
- **Testing**: pytest
- **Architecture**: Clean separation of concerns

---

## 📚 Documentation

- [`README_DEMO.md`](README_DEMO.md) - Complete demo guide
- [`HOW_TO_CHECK_LEARNING.md`](HOW_TO_CHECK_LEARNING.md) - Learning verification
- [`HOW_TO_CHECK_EXECUTION.md`](HOW_TO_CHECK_EXECUTION.md) - Execution verification
- [`RUNTIME_CONFIG_DEMO.md`](RUNTIME_CONFIG_DEMO.md) - Config change guide

---

## ❓ FAQ

**Q: Does it use real payment data?**  
A: No, simulated for safety. Realistic and configurable.

**Q: Does it modify source code?**  
A: No, only runtime configuration. Production-safe.

**Q: How does learning work?**  
A: Deterministic rules based on past outcomes. No neural network training.

**Q: Can it run without Gemini?**  
A: Yes! Core logic is deterministic. LLM only adds explanations.

**Q: Is this production-ready?**  
A: Core is production-ready. Needs deployment infrastructure for full production.

---

## 🎯 For Judges/Reviewers

### What Makes This Special?

1. **Complete Agentic Loop** - Not just AI reasoning, but full observe-decide-act-learn cycle
2. **Production-Grade** - Comprehensive testing, error handling, logging
3. **Safe by Design** - Approval guardrails, reversible actions, bounded learning
4. **Deterministic Core** - Works without LLM, explainable decisions
5. **Real Impact** - Measurable improvements (+13% success rate)

### Run This First

```bash
PYTHONPATH=. python FULL_DEMO.py
```

Press ENTER to advance through each stage. Takes ~5 minutes.

---

## 📊 System Status

- ✅ Steps 1-7 Complete
- ✅ 18+ Tests Passing
- ✅ Full Agentic Loop Working
- ✅ Learning Active
- ✅ Production-Ready Core

---

## 🚀 Next Steps (Future Work)

- [ ] REST API endpoints
- [ ] Monitoring dashboard
- [ ] Human approval workflow UI
- [ ] Database persistence
- [ ] Rollback mechanism
- [ ] Multi-agent coordination

---

## 📝 License

[Your License Here]

---

## 🙏 Acknowledgments

Built with:
- Google Gemini 2.5 Flash
- Python 3.12
- pytest

---

**READY TO DEMO** ✨

Run `FULL_DEMO.py` to see the complete system in action!

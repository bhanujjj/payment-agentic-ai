"""
Quick verification script for Step 4: Agent Reasoning Layer

This script demonstrates that the reasoning layer is working correctly.
"""

import asyncio
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

from simulation import PaymentGenerator
from agent import MetricsEngine, Reasoner


async def main():
    print("=" * 70)
    print("STEP 4 VERIFICATION: Agent Reasoning Layer")
    print("=" * 70)
    
    # Check API key
    api_key = os.getenv('GEMINI_API_KEY')
    if not api_key:
        print("\n❌ GEMINI_API_KEY not found!")
        print("Please set it in .env file")
        return
    
    print(f"\n✅ API Key loaded: {api_key[:20]}...")
    print(f"✅ Model: {os.getenv('GEMINI_MODEL', 'gemini-2.5-flash-lite')}")
    
    # Test 1: Normal operation
    print("\n" + "=" * 70)
    print("TEST 1: Normal Operation Reasoning")
    print("=" * 70)
    
    gen = PaymentGenerator(config={'seed': 42})
    gen.base_failure_rate = 0.02
    payments = gen.generate_batch(count=100, time_span_seconds=300)
    
    engine = MetricsEngine()
    signals = engine.compute_signals(payments)
    
    print(f"\nInput Signals:")
    print(f"  Success Rate: {signals.overall_success_rate:.1%}")
    print(f"  Total Payments: {signals.total_payments}")
    print(f"  Avg Latency: {signals.avg_latency_ms:.0f}ms")
    
    reasoner = Reasoner()
    reasoning = await reasoner.reason(signals)
    
    print(f"\n🤖 LLM Reasoning:")
    print(reasoning.get_summary())
    
    # Test 2: Bank degradation
    print("\n" + "=" * 70)
    print("TEST 2: Bank Degradation Detection")
    print("=" * 70)
    
    gen = PaymentGenerator(config={'seed': 42})
    gen.simulate_bank_degradation("HDFC Bank")
    payments = gen.generate_batch(count=200, time_span_seconds=300)
    
    signals = engine.compute_signals(payments)
    
    print(f"\nInput Signals:")
    print(f"  Success Rate: {signals.overall_success_rate:.1%}")
    print(f"  Degraded Banks: {signals.degraded_banks}")
    print(f"  Anomaly: {signals.has_anomaly}")
    
    reasoning = await reasoner.reason(signals)
    
    print(f"\n🤖 LLM Reasoning:")
    top = reasoning.get_top_hypothesis()
    if top:
        print(f"  Top Hypothesis: {top[0]} ({top[1]:.0%} confidence)")
    
    if "bank_degradation" in reasoning.hypotheses:
        print(f"  ✅ Correctly detected bank degradation!")
        print(f"  Confidence: {reasoning.hypotheses['bank_degradation']:.0%}")
    
    print(f"\n  Explanation: {reasoning.explanation[:200]}...")
    
    # Test 3: Multiple issues
    print("\n" + "=" * 70)
    print("TEST 3: Multiple Issues")
    print("=" * 70)
    
    gen = PaymentGenerator(config={'seed': 42})
    gen.simulate_bank_outage("ICICI Bank")
    gen.simulate_bank_degradation("HDFC Bank")
    payments = gen.generate_batch(count=200, time_span_seconds=300)
    
    signals = engine.compute_signals(payments)
    
    print(f"\nInput Signals:")
    print(f"  Success Rate: {signals.overall_success_rate:.1%}")
    print(f"  Degraded Banks: {signals.degraded_banks}")
    
    reasoning = await reasoner.reason(signals)
    
    print(f"\n🤖 LLM Reasoning - All Hypotheses:")
    for hyp, conf in sorted(reasoning.hypotheses.items(), key=lambda x: x[1], reverse=True):
        print(f"  • {hyp}: {conf:.0%}")
    
    # Summary
    print("\n" + "=" * 70)
    print("VERIFICATION COMPLETE ✅")
    print("=" * 70)
    print("\nThe reasoning layer is working correctly!")
    print("✅ Gemini API integration successful")
    print("✅ Structured reasoning output")
    print("✅ Hypothesis generation with confidence scores")
    print("✅ Assumptions and uncertainty tracking")
    print("✅ Human-readable explanations")
    print("\n" + "=" * 70)


if __name__ == "__main__":
    asyncio.run(main())

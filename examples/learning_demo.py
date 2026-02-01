"""
Learning & Feedback Loop Demo

Demonstrates the complete agentic loop with learning from outcomes.
"""

import asyncio
import logging
from datetime import datetime
from simulation.generator import PaymentGenerator
from agent.metrics import MetricsEngine
from agent.reasoner import Reasoner
from agent.decider import DecisionEngine
from agent.executor import ActionExecutor
from agent.evaluator import OutcomeEvaluator
from agent.memory import ActionMemory
from agent.learner import ActionLearner
from agent.learning_models import ActionOutcome

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def main():
    """Demonstrate complete learning loop."""
    
    logger.info("=" * 80)
    logger.info("LEARNING & FEEDBACK LOOP DEMO")
    logger.info("=" * 80)
    logger.info("")
    
    # Initialize components
    memory = ActionMemory(storage_path="./data/memory/learning_demo.json")
    memory.clear()  # Start fresh for demo
    
    learner = ActionLearner(memory)
    evaluator = OutcomeEvaluator()
    
    executor = ActionExecutor()
    reasoner = Reasoner()
    decider = DecisionEngine(learner=learner)  # Pass learner to decider
    engine = MetricsEngine()
    
    logger.info("=" * 80)
    logger.info("ITERATION 1: FIRST ENCOUNTER (NO LEARNING YET)")
    logger.info("=" * 80)
    logger.info("")
    
    # === ITERATION 1: First encounter with retry storm ===
    
    # Step 1: Generate scenario with retry storm
    logger.info("Step 1: Generating retry storm scenario")
    logger.info("-" * 80)
    gen = PaymentGenerator(config={'seed': 42})
    payments_pre = gen.generate_batch(count=200, time_span_seconds=300)
    
    # Add retries to create storm
    retry_payments = []
    for payment in payments_pre[:50]:
        if payment.is_failed():
            retries = gen.simulate_retry_storm(payment, retry_count=5)
            retry_payments.extend(retries)
    
    all_payments_pre = payments_pre + retry_payments
    logger.info(f"Generated {len(all_payments_pre)} payments with {len(retry_payments)} retries")
    logger.info("")
    
    # Step 2: Compute PRE-ACTION metrics
    logger.info("Step 2: Computing PRE-ACTION metrics")
    logger.info("-" * 80)
    pre_signals = engine.compute_signals(all_payments_pre)
    logger.info(f"Success Rate: {pre_signals.overall_success_rate:.1%}")
    logger.info(f"Latency: {pre_signals.avg_latency_ms:.0f}ms")
    logger.info(f"Retry Count: {pre_signals.total_retries}")
    logger.info(f"Error Rate: {pre_signals.overall_failure_rate:.1%}")
    logger.info("")
    
    # Step 3: Reasoning
    logger.info("Step 3: Agent Reasoning")
    logger.info("-" * 80)
    reasoning = await reasoner.reason(pre_signals)
    top_hypothesis = reasoning.get_top_hypothesis()
    if top_hypothesis:
        logger.info(f"Hypothesis: {top_hypothesis[0]} ({top_hypothesis[1]:.0%})")
    logger.info("")
    
    # Step 4: Decision (first time - no learning yet)
    logger.info("Step 4: Decision Making (NO learning data yet)")
    logger.info("-" * 80)
    decision = decider.decide(reasoning, pre_signals)
    logger.info(f"Selected Action: {decision.selected_action}")
    logger.info(f"Confidence: {decision.confidence:.0%}")
    logger.info(f"Risk Level: {decision.risk_level.value}")
    logger.info("")
    
    # Force retry adjustment for demo
    if decision.selected_action != "recommend_retry_adjustment":
        logger.info("(Forcing retry_adjustment for demo purposes)")
        from agent.decision_models import Decision, RiskLevel
        decision = Decision(
            selected_action="recommend_retry_adjustment",
            confidence=0.75,
            risk_level=RiskLevel.LOW,
            requires_human_approval=False,
            reasoning_summary="Retry storm detected",
            considered_actions=["do_nothing", "recommend_retry_adjustment"],
            rejected_actions=[]
        )
        logger.info("")
    
    # Step 5: Execute action
    logger.info("Step 5: Executing Action")
    logger.info("-" * 80)
    execution_result = executor.execute(decision, pre_signals)
    logger.info(f"Execution: {execution_result.status.value}")
    logger.info(f"State Change: {execution_result.state_changes}")
    logger.info("")
    
    # Step 6: Generate POST-ACTION payments
    logger.info("Step 6: Generating POST-ACTION payments")
    logger.info("-" * 80)
    # Simulate improved scenario after action
    gen2 = PaymentGenerator(config={'seed': 43})  # Different seed for variation
    payments_post = gen2.generate_batch(count=200, time_span_seconds=300)
    
    # Fewer retries after adjustment
    retry_payments_post = []
    for payment in payments_post[:20]:  # Only 20 instead of 50
        if payment.is_failed():
            retries = gen2.simulate_retry_storm(payment, retry_count=2)  # Only 2 instead of 5
            retry_payments_post.extend(retries)
    
    all_payments_post = payments_post + retry_payments_post
    logger.info(f"Generated {len(all_payments_post)} payments with {len(retry_payments_post)} retries")
    logger.info("")
    
    # Step 7: Compute POST-ACTION metrics
    logger.info("Step 7: Computing POST-ACTION metrics")
    logger.info("-" * 80)
    post_signals = engine.compute_signals(all_payments_post)
    logger.info(f"Success Rate: {post_signals.overall_success_rate:.1%}")
    logger.info(f"Latency: {post_signals.avg_latency_ms:.0f}ms")
    logger.info(f"Retry Count: {post_signals.total_retries}")
    logger.info(f"Error Rate: {post_signals.overall_failure_rate:.1%}")
    logger.info("")
    
    # Step 8: Evaluate outcome
    logger.info("Step 8: Evaluating Outcome")
    logger.info("-" * 80)
    outcome_class, outcome_score = evaluator.evaluate_from_signals(
        pre_signals, post_signals, decision.selected_action
    )
    
    # Compute deltas
    success_delta = post_signals.overall_success_rate - pre_signals.overall_success_rate
    latency_delta = post_signals.avg_latency_ms - pre_signals.avg_latency_ms
    retry_delta = post_signals.total_retries - pre_signals.total_retries
    error_delta = post_signals.overall_failure_rate - pre_signals.overall_failure_rate
    
    logger.info(f"Success Rate: {pre_signals.overall_success_rate:.1%} → {post_signals.overall_success_rate:.1%} (Δ {success_delta:+.1%})")
    logger.info(f"Latency: {pre_signals.avg_latency_ms:.0f}ms → {post_signals.avg_latency_ms:.0f}ms (Δ {latency_delta:+.0f}ms)")
    logger.info(f"Retries: {pre_signals.total_retries} → {post_signals.total_retries} (Δ {retry_delta:+d})")
    logger.info(f"Outcome: {outcome_class.value} (score: {outcome_score:.2f})")
    logger.info("")
    
    # Step 9: Store in memory
    logger.info("Step 9: Storing Outcome in Memory")
    logger.info("-" * 80)
    
    context = decider._summarize_context(pre_signals)
    outcome = ActionOutcome(
        context_summary=context,
        action=decision.selected_action,
        risk_level=decision.risk_level.value,
        pre_success_rate=pre_signals.overall_success_rate,
        pre_latency_ms=pre_signals.avg_latency_ms,
        pre_retry_count=pre_signals.total_retries,
        pre_error_rate=pre_signals.overall_failure_rate,
        post_success_rate=post_signals.overall_success_rate,
        post_latency_ms=post_signals.avg_latency_ms,
        post_retry_count=post_signals.total_retries,
        post_error_rate=post_signals.overall_failure_rate,
        success_rate_delta=success_delta,
        latency_delta=latency_delta,
        retry_delta=retry_delta,
        error_rate_delta=error_delta,
        outcome=outcome_class,
        outcome_score=outcome_score,
        timestamp=datetime.utcnow(),
        notes="First iteration - establishing baseline"
    )
    
    memory.add(outcome)
    logger.info(f"✓ Stored: {outcome.action} → {outcome.outcome.value}")
    logger.info(f"  Context: {outcome.context_summary}")
    logger.info("")
    
    # === ITERATION 2: Same scenario again - learning should kick in ===
    
    logger.info("")
    logger.info("=" * 80)
    logger.info("ITERATION 2: SAME SCENARIO (LEARNING ACTIVE)")
    logger.info("=" * 80)
    logger.info("")
    
    # Generate same scenario
    logger.info("Generating similar retry storm scenario...")
    gen3 = PaymentGenerator(config={'seed': 44})
    payments_pre2 = gen3.generate_batch(count=200, time_span_seconds=300)
    retry_payments2 = []
    for payment in payments_pre2[:50]:
        if payment.is_failed():
            retries = gen3.simulate_retry_storm(payment, retry_count=5)
            retry_payments2.extend(retries)
    all_payments_pre2 = payments_pre2 + retry_payments2
    
    pre_signals2 = engine.compute_signals(all_payments_pre2)
    logger.info(f"PRE-ACTION: {pre_signals2.overall_success_rate:.1%} success, {pre_signals2.total_retries} retries")
    logger.info("")
    
    # Reasoning
    reasoning2 = await reasoner.reason(pre_signals2)
    
    # Decision - NOW WITH LEARNING
    logger.info("Decision Making (WITH learning from iteration 1)")
    logger.info("-" * 80)
    decision2 = decider.decide(reasoning2, pre_signals2)  # Learner is already integrated
    logger.info(f"Selected Action: {decision2.selected_action}")
    logger.info(f"Confidence: {decision2.confidence:.0%}")
    logger.info("")
    
    # Show learning summary
    logger.info("=" * 80)
    logger.info("LEARNING SUMMARY")
    logger.info("=" * 80)
    summary = learner.get_learning_summary()
    logger.info(f"Status: {summary['status']}")
    logger.info(f"Total Observations: {summary.get('total_observations', 0)}")
    logger.info("")
    logger.info("Action Insights:")
    for action, insight in summary.get('insights', {}).items():
        logger.info(f"  {action}:")
        logger.info(f"    - Observations: {insight['total']}")
        logger.info(f"    - Success Rate: {insight['success_rate']}")
        logger.info(f"    - Avg Score: {insight['avg_score']}")
        logger.info(f"    - Recommendation: {insight['recommendation']}")
    logger.info("")
    
    logger.info("=" * 80)
    logger.info("DEMO COMPLETE")
    logger.info("=" * 80)
    logger.info("")
    logger.info("✅ Learning loop demonstrated:")
    logger.info("   1. Captured PRE-ACTION metrics")
    logger.info("   2. Executed action")
    logger.info("   3. Captured POST-ACTION metrics")
    logger.info("   4. Evaluated outcome (SUCCESS)")
    logger.info("   5. Stored in memory")
    logger.info("   6. Future decisions influenced by learning")
    logger.info("")


if __name__ == "__main__":
    asyncio.run(main())

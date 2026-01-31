import asyncio
from simulation.generator import PaymentGenerator
from agent.metrics import MetricsEngine
from agent.reasoner import Reasoner
from agent.decider import DecisionEngine

async def test():
    print('\n' + '=' * 70)
    print('ANALYZING WHY DECISIONS ARE do_nothing')
    print('=' * 70 + '\n')
    
    # Severe scenario: 2 banks down
    gen = PaymentGenerator(config={'seed': 42})
    gen.simulate_bank_outage('HDFC Bank')
    gen.simulate_bank_outage('ICICI Bank')
    payments = gen.generate_batch(count=200, time_span_seconds=300)
    
    engine = MetricsEngine()
    signals = engine.compute_signals(payments)
    
    print(f'📊 SEVERE SCENARIO:')
    print(f'   Success Rate: {signals.overall_success_rate:.1%}')
    print(f'   Outages: HDFC + ICICI')
    print(f'   This is BAD - we should reroute!\n')
    
    reasoner = Reasoner()
    reasoning = await reasoner.reason(signals)
    
    decider = DecisionEngine()
    decision = decider.decide(reasoning, signals)
    
    print(f'🎯 DECISION: {decision.selected_action}')
    print(f'   Confidence: {decision.confidence:.0%}\n')
    
    print('📋 ALL ACTION SCORES:')
    for action in decision.considered_actions:
        print(f'   {action.action:30s} {action.score:.1%} (risk: {action.risk_level.value})')
        print(f'      Expected success impact: {action.expected_success_rate_impact:+.0%}')
    
    print('\n' + '=' * 70)
    print('PROBLEM: Actions have low scores even in severe scenarios')
    print('=' * 70)

asyncio.run(test())

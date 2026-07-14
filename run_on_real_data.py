"""
CLI Runner to run Payment Routing Agent on real transaction data.

Allows loading a CSV or JSON file of transaction logs, segments them into time windows,
and executes the observe-decide-act-learn agent loop sequentially.
"""

import csv
import argparse
import asyncio
import logging
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Any

from agent.core import PaymentAgent
from utils.data_loader import load_payment_records
from simulation.models import PaymentRecord, PaymentMethod, PaymentStatus, ErrorCode

# Configure logging to show agent flow clearly in console
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    stream=sys.stdout
)
logger = logging.getLogger("RealDataRunner")


def generate_sample_csv(file_path: Path):
    """Generates a realistic sample CSV transaction file representing a degradation and recovery."""
    logger.info(f"Generating sample transaction file at: {file_path}")
    file_path.parent.mkdir(parents=True, exist_ok=True)
    
    start_time = datetime.now() - timedelta(hours=1)
    
    headers = [
        "transaction_id", "timestamp", "method", "provider", "amount", 
        "currency", "status", "error", "duration_ms", "retries", "merchant"
    ]
    
    rows = []
    
    # Segment 1: Window 1 (Minutes 0-5) - Healthy Operation
    # 60 transactions, 95% success rate, low latency
    for i in range(60):
        t_time = start_time + timedelta(seconds=i * 5)
        provider = "HDFC Bank" if i % 2 == 0 else "ICICI Bank"
        status = "SUCCESS"
        error = "NONE"
        duration = int(120 + (i % 10) * 15)
        
        # 5% fail rate
        if i % 20 == 0:
            status = "FAILED"
            error = "INSUFFICIENT_FUNDS"
            
        rows.append([
            f"tx_healthy_{i}", t_time.isoformat(), "UPI", provider, 250.0,
            "INR", status, error, duration, 0, "merchant_1"
        ])
        
    # Segment 2: Window 2 (Minutes 5-10) - ICICI Bank Degradation (Timeout storm)
    # 60 transactions, ICICI Bank starts failing with timeouts, high retries
    for i in range(60):
        t_time = start_time + timedelta(minutes=5, seconds=i * 5)
        provider = "HDFC Bank" if i % 2 == 0 else "ICICI Bank"
        status = "SUCCESS"
        error = "NONE"
        duration = 150
        retries = 0
        
        if provider == "ICICI Bank":
            # 80% fail rate for ICICI Bank due to timeouts
            if i % 5 != 0:
                status = "TIMEOUT"
                error = "BANK_TIMEOUT"
                duration = 3000  # Timeout latency
                retries = 3
            else:
                status = "SUCCESS"
                duration = 400
        else:
            # HDFC remains healthy
            if i % 20 == 0:
                status = "FAILED"
                error = "INSUFFICIENT_FUNDS"
                
        rows.append([
            f"tx_degraded_{i}", t_time.isoformat(), "UPI", provider, 500.0,
            "INR", status, error, duration, retries, "merchant_1"
        ])

    # Segment 3: Window 3 (Minutes 10-15) - Post Action Phase
    # The agent executes 'recommend_reroute' away from ICICI Bank
    # Only HDFC Bank gets the traffic, and success rate recovers
    for i in range(60):
        t_time = start_time + timedelta(minutes=10, seconds=i * 5)
        # Rerouted traffic means all traffic goes to HDFC Bank
        provider = "HDFC Bank"
        status = "SUCCESS"
        error = "NONE"
        duration = int(140 + (i % 8) * 12)
        
        # 5% fail rate (normal background noise)
        if i % 20 == 0:
            status = "FAILED"
            error = "INSUFFICIENT_FUNDS"
            
        rows.append([
            f"tx_recovered_{i}", t_time.isoformat(), "UPI", provider, 1000.0,
            "INR", status, error, duration, 0, "merchant_1"
        ])

    with open(file_path, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(headers)
        writer.writerows(rows)
    logger.info("Sample transaction file generated successfully.")


def print_window_report(win_idx: int, start: datetime, end: datetime, res: Dict[str, Any]):
    """Pretty prints the metrics, reasoning, and decision for a single window."""
    signals = res["signals"]
    reasoning = res["reasoning"]
    decision = res["decision"]
    execution = res["execution"]
    learning = res["learning"]
    
    print("\n" + "=" * 90)
    print(f" 📊 WINDOW #{win_idx+1} REPORT | {start.strftime('%H:%M:%S')} - {end.strftime('%H:%M:%S')}")
    print("=" * 90)
    
    # 1. Metrics
    print("\n[SYSTEM METRICS]")
    print(f"  • Total Payments        : {signals.total_payments}")
    print(f"  • Success Rate          : {signals.overall_success_rate:.1%}")
    print(f"  • Failure Rate          : {signals.overall_failure_rate:.1%}")
    print(f"  • Average Latency       : {signals.avg_latency_ms:.0f}ms")
    print(f"  • Total Retries         : {signals.total_retries}")
    print(f"  • Retry Effectiveness   : {signals.retry_effectiveness:.2f}")
    if signals.degraded_banks:
        print(f"  • Degraded Providers    : 🔴 {', '.join(signals.degraded_banks)}")
    else:
        print("  • Degraded Providers    : 🟢 None")
        
    # 2. Learning
    if learning:
        print("\n[LEARNING ACTION EVALUATION]")
        if "error" in learning:
            print(f"  ⚠️ Error calculating learning: {learning['error']}")
        else:
            success_status = "✅ SUCCESS" if learning["success"] else "❌ FAILURE"
            print(f"  • Evaluated Action      : {learning['action']}")
            print(f"  • Outcome Score         : {learning['outcome']['outcome_score']:.2f} ({success_status})")
            print(f"  • Latency Change        : {learning['outcome'].get('latency_delta', 0):+.0f}ms")
            print(f"  • Success Rate Change   : {learning['outcome'].get('success_rate_delta', 0.0):+.1%}")
            
    # 3. AI Reasoning
    print("\n[🤖 LLM REASONING & DIAGNOSIS]")
    print(f"  • Explanation           : {reasoning.explanation}")
    top_hyp = reasoning.get_top_hypothesis()
    if top_hyp:
        print(f"  • Primary Hypothesis    : {top_hyp[0]} ({top_hyp[1]:.0%} confidence)")
        
    # 4. Decision & Action
    print("\n[🎯 AGENT DECISION & ROUTING ACTION]")
    print(f"  • Selected Action       : {decision.selected_action}")
    print(f"  • Confidence Score      : {decision.confidence:.0%}")
    print(f"  • Risk Level            : {decision.risk_level.value}")
    print(f"  • Human Approval Needed : {'YES ⚠️' if decision.requires_human_approval else 'NO ✅'}")
    
    # 5. Execution State
    print("\n[⚙️ ACTION EXECUTION STATUS]")
    print(f"  • Status                : {execution.status.value}")
    if execution.expected_effect:
        print(f"  • Expected Effect       : {execution.expected_effect}")
    if execution.error:
        print(f"  • Execution Error       : {execution.error}")
        
    print("\n" + "-" * 90)


async def main():
    parser = argparse.ArgumentParser(description="Run Payment Routing Agent on real transaction history.")
    parser.add_argument(
        "--file", 
        type=str, 
        default="examples/sample_transactions.csv",
        help="Path to CSV or JSON transaction log file."
    )
    parser.add_argument(
        "--window", 
        type=int, 
        default=300,
        help="Time window duration in seconds (default: 300s / 5 minutes)."
    )
    parser.add_argument(
        "--memory-path", 
        type=str, 
        default="./data/memory/real_data_memory.json",
        help="Persistent path for the learning memory database."
    )
    args = parser.parse_args()
    
    file_path = Path(args.file)
    
    # Generate sample data if not present
    if not file_path.exists() and args.file == "examples/sample_transactions.csv":
        generate_sample_csv(file_path)
        
    if not file_path.exists():
        logger.error(f"File not found: {args.file}")
        sys.exit(1)
        
    logger.info(f"Loading transaction records from {file_path}...")
    try:
        records = load_payment_records(file_path)
    except Exception as e:
        logger.error(f"Failed to load payment records: {e}", exc_info=True)
        sys.exit(1)
        
    if not records:
        logger.error("No transactions found in file.")
        sys.exit(1)
        
    # Segment records into time windows
    logger.info(f"Segmenting {len(records)} records into {args.window}s time windows...")
    windows: List[List[PaymentRecord]] = []
    window_boundaries: List[tuple] = []
    
    start_time = records[0].timestamp
    current_win_records = []
    current_boundary_start = start_time
    window_duration = timedelta(seconds=args.window)
    
    for record in records:
        # If record timestamp falls outside current window boundary, close and advance window
        while record.timestamp >= current_boundary_start + window_duration:
            windows.append(current_win_records)
            window_boundaries.append((current_boundary_start, current_boundary_start + window_duration))
            current_win_records = []
            current_boundary_start += window_duration
            
        current_win_records.append(record)
        
    if current_win_records:
        windows.append(current_win_records)
        window_boundaries.append((current_boundary_start, current_boundary_start + window_duration))
        
    logger.info(f"Created {len(windows)} execution windows.")
    
    # Initialize the agent
    config = {
        "memory": {"path": args.memory_path},
        "llm": {
            "gemini_api_key": os.getenv("GEMINI_API_KEY"),
            "gemini_model": os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
        }
    }
    
    agent = PaymentAgent(config=config)
    
    print("\n" + "=" * 90)
    print(" 🚀 STARTING PAYMENT ROUTING AGENT RUN ON REAL DATA")
    print("=" * 90)
    
    for idx, win_records in enumerate(windows):
        win_start, win_end = window_boundaries[idx]
        if not win_records:
            logger.info(f"Window #{idx+1} ({win_start.strftime('%H:%M:%S')} - {win_end.strftime('%H:%M:%S')}): No transaction activity.")
            continue
            
        logger.info(f"Executing Window #{idx+1} with {len(win_records)} transactions...")
        
        # Execute the agent step (observes current window, runs learning, reasons, decides, acts)
        res = await agent.run_step(win_records)
        
        # Display the execution report for the window
        print_window_report(idx, win_start, win_end, res)
        
        # Pause slightly between windows for readability
        await asyncio.sleep(1.0)
        
    print("\n" + "=" * 90)
    print(" 🎉 ROUTING RUN COMPLETED SUCCESSFULLY")
    print(f" Persistent memory database saved to: {args.memory_path}")
    print("=" * 90 + "\n")


if __name__ == "__main__":
    asyncio.run(main())

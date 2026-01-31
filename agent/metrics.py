"""
Metrics Engine - Aggregates payment data into actionable signals.

This module converts raw payment records into high-level metrics
that the agent can reason over.
"""

import logging
from typing import List, Dict, Optional
from datetime import datetime, timedelta
from collections import defaultdict, Counter
import statistics

from simulation.models import PaymentRecord, PaymentStatus, ErrorCode
from agent.signals import PaymentSignals, Trend, Severity, BankSignal


class MetricsEngine:
    """
    Aggregates payment data into signals over time windows.
    
    This is the bridge between raw payment data and agent reasoning.
    """
    
    def __init__(self, config: Optional[Dict] = None):
        """
        Initialize metrics engine.
        
        Args:
            config: Configuration dictionary with:
                - degradation_threshold: Failure rate to mark as degraded (default: 0.3)
                - critical_threshold: Failure rate to mark as critical (default: 0.5)
                - latency_threshold_ms: High latency threshold (default: 1000)
        """
        self.config = config or {}
        self.logger = logging.getLogger(__name__)
        
        # Thresholds
        self.degradation_threshold = self.config.get('degradation_threshold', 0.3)
        self.critical_threshold = self.config.get('critical_threshold', 0.5)
        self.latency_threshold_ms = self.config.get('latency_threshold_ms', 1000)
        
        # Historical data for trend analysis
        self.historical_signals: List[PaymentSignals] = []
        self.max_history = 10  # Keep last 10 windows
        
    def compute_signals(
        self,
        payments: List[PaymentRecord],
        window_duration_seconds: int = 300
    ) -> PaymentSignals:
        """
        Compute signals from a list of payment records.
        
        Args:
            payments: List of payment records
            window_duration_seconds: Duration of the time window
            
        Returns:
            Computed payment signals
        """
        if not payments:
            return self._empty_signals(window_duration_seconds)
        
        # Determine time window
        timestamps = [p.timestamp for p in payments]
        window_start = min(timestamps)
        window_end = max(timestamps)
        
        # Basic counts
        total = len(payments)
        successful = sum(1 for p in payments if p.is_successful())
        failed = sum(1 for p in payments if p.is_failed())
        
        # Success/failure rates
        success_rate = successful / total if total > 0 else 0.0
        failure_rate = failed / total if total > 0 else 0.0
        
        # Compute bank-specific metrics
        bank_metrics = self._compute_bank_metrics(payments)
        
        # Compute payment method metrics
        method_metrics = self._compute_method_metrics(payments)
        
        # Compute latency metrics
        latency_metrics = self._compute_latency_metrics(payments)
        
        # Compute retry metrics
        retry_metrics = self._compute_retry_metrics(payments)
        
        # Compute error distribution
        error_metrics = self._compute_error_metrics(payments)
        
        # Detect anomalies
        anomaly_info = self._detect_anomalies(
            success_rate,
            bank_metrics,
            latency_metrics
        )
        
        # Compute trends
        trends = self._compute_trends(
            latency_metrics['avg_latency_ms'],
            total,
            failure_rate
        )
        
        # Identify degraded entities
        degraded_banks = [
            bank for bank, metrics in bank_metrics.items()
            if metrics['failure_rate'] > self.degradation_threshold
        ]
        
        degraded_methods = [
            method for method, metrics in method_metrics.items()
            if metrics['failure_rate'] > self.degradation_threshold
        ]
        
        # Create signals object
        signals = PaymentSignals(
            window_start=window_start.isoformat(),
            window_end=window_end.isoformat(),
            window_duration_seconds=window_duration_seconds,
            total_payments=total,
            successful_payments=successful,
            failed_payments=failed,
            overall_success_rate=success_rate,
            overall_failure_rate=failure_rate,
            bank_failure_rates={
                bank: metrics['failure_rate']
                for bank, metrics in bank_metrics.items()
            },
            bank_avg_latencies={
                bank: metrics['avg_latency']
                for bank, metrics in bank_metrics.items()
            },
            bank_volumes={
                bank: metrics['count']
                for bank, metrics in bank_metrics.items()
            },
            method_failure_rates={
                method: metrics['failure_rate']
                for method, metrics in method_metrics.items()
            },
            method_avg_latencies={
                method: metrics['avg_latency']
                for method, metrics in method_metrics.items()
            },
            method_volumes={
                method: metrics['count']
                for method, metrics in method_metrics.items()
            },
            avg_latency_ms=latency_metrics['avg_latency_ms'],
            p50_latency_ms=latency_metrics['p50_latency_ms'],
            p95_latency_ms=latency_metrics['p95_latency_ms'],
            p99_latency_ms=latency_metrics['p99_latency_ms'],
            latency_trend=trends['latency_trend'],
            volume_trend=trends['volume_trend'],
            failure_rate_trend=trends['failure_rate_trend'],
            total_retries=retry_metrics['total_retries'],
            retry_success_rate=retry_metrics['retry_success_rate'],
            retry_effectiveness=retry_metrics['retry_effectiveness'],
            error_code_counts=error_metrics['error_counts'],
            top_errors=error_metrics['top_errors'],
            has_anomaly=anomaly_info['has_anomaly'],
            anomaly_severity=anomaly_info['severity'],
            anomaly_description=anomaly_info['description'],
            degraded_banks=degraded_banks,
            degraded_methods=degraded_methods
        )
        
        # Store in history for trend analysis
        self.historical_signals.append(signals)
        if len(self.historical_signals) > self.max_history:
            self.historical_signals.pop(0)
        
        return signals
    
    def _compute_bank_metrics(
        self,
        payments: List[PaymentRecord]
    ) -> Dict[str, Dict]:
        """Compute per-bank metrics."""
        bank_data = defaultdict(list)
        
        for payment in payments:
            bank_data[payment.bank].append(payment)
        
        metrics = {}
        for bank, bank_payments in bank_data.items():
            total = len(bank_payments)
            failed = sum(1 for p in bank_payments if p.is_failed())
            latencies = [p.latency_ms for p in bank_payments]
            
            metrics[bank] = {
                'count': total,
                'failure_rate': failed / total if total > 0 else 0.0,
                'avg_latency': statistics.mean(latencies) if latencies else 0.0
            }
        
        return metrics
    
    def _compute_method_metrics(
        self,
        payments: List[PaymentRecord]
    ) -> Dict[str, Dict]:
        """Compute per-payment-method metrics."""
        method_data = defaultdict(list)
        
        for payment in payments:
            method_data[payment.payment_method.value].append(payment)
        
        metrics = {}
        for method, method_payments in method_data.items():
            total = len(method_payments)
            failed = sum(1 for p in method_payments if p.is_failed())
            latencies = [p.latency_ms for p in method_payments]
            
            metrics[method] = {
                'count': total,
                'failure_rate': failed / total if total > 0 else 0.0,
                'avg_latency': statistics.mean(latencies) if latencies else 0.0
            }
        
        return metrics
    
    def _compute_latency_metrics(
        self,
        payments: List[PaymentRecord]
    ) -> Dict[str, float]:
        """Compute latency percentiles."""
        latencies = sorted([p.latency_ms for p in payments])
        
        if not latencies:
            return {
                'avg_latency_ms': 0.0,
                'p50_latency_ms': 0.0,
                'p95_latency_ms': 0.0,
                'p99_latency_ms': 0.0
            }
        
        return {
            'avg_latency_ms': statistics.mean(latencies),
            'p50_latency_ms': self._percentile(latencies, 50),
            'p95_latency_ms': self._percentile(latencies, 95),
            'p99_latency_ms': self._percentile(latencies, 99)
        }
    
    def _compute_retry_metrics(
        self,
        payments: List[PaymentRecord]
    ) -> Dict:
        """Compute retry-related metrics."""
        retries = [p for p in payments if p.retry_count > 0]
        original_attempts = [p for p in payments if p.retry_count == 0]
        
        total_retries = len(retries)
        
        if total_retries == 0:
            return {
                'total_retries': 0,
                'retry_success_rate': 0.0,
                'retry_effectiveness': 0.0
            }
        
        # Retry success rate
        retry_successes = sum(1 for p in retries if p.is_successful())
        retry_success_rate = retry_successes / total_retries if total_retries > 0 else 0.0
        
        # Retry effectiveness: compare retry success rate to original success rate
        original_successes = sum(1 for p in original_attempts if p.is_successful())
        original_success_rate = original_successes / len(original_attempts) if original_attempts else 0.0
        
        # Positive = retries are helping, negative = retries are hurting
        retry_effectiveness = retry_success_rate - original_success_rate
        
        return {
            'total_retries': total_retries,
            'retry_success_rate': retry_success_rate,
            'retry_effectiveness': retry_effectiveness
        }
    
    def _compute_error_metrics(
        self,
        payments: List[PaymentRecord]
    ) -> Dict:
        """Compute error distribution."""
        failed_payments = [p for p in payments if p.is_failed()]
        
        error_counts = Counter(
            p.error_code.value for p in failed_payments
            if p.error_code != ErrorCode.NONE
        )
        
        # Get top 5 errors
        top_errors = [error for error, _ in error_counts.most_common(5)]
        
        return {
            'error_counts': dict(error_counts),
            'top_errors': top_errors
        }
    
    def _detect_anomalies(
        self,
        success_rate: float,
        bank_metrics: Dict,
        latency_metrics: Dict
    ) -> Dict:
        """Detect anomalies in the data."""
        has_anomaly = False
        severity = Severity.NORMAL
        descriptions = []
        
        # Check overall success rate
        if success_rate < 0.5:
            has_anomaly = True
            severity = Severity.CRITICAL
            descriptions.append(f"Critical: Overall success rate {success_rate:.1%}")
        elif success_rate < 0.7:
            has_anomaly = True
            severity = Severity.WARNING
            descriptions.append(f"Warning: Low success rate {success_rate:.1%}")
        
        # Check for bank issues
        for bank, metrics in bank_metrics.items():
            if metrics['failure_rate'] > self.critical_threshold:
                has_anomaly = True
                if severity != Severity.CRITICAL:
                    severity = Severity.CRITICAL
                descriptions.append(f"Critical: {bank} failure rate {metrics['failure_rate']:.1%}")
            elif metrics['failure_rate'] > self.degradation_threshold:
                has_anomaly = True
                if severity == Severity.NORMAL:
                    severity = Severity.WARNING
                descriptions.append(f"Warning: {bank} degraded")
        
        # Check latency
        if latency_metrics['p95_latency_ms'] > self.latency_threshold_ms:
            has_anomaly = True
            if severity == Severity.NORMAL:
                severity = Severity.WARNING
            descriptions.append(f"High latency: P95 {latency_metrics['p95_latency_ms']:.0f}ms")
        
        return {
            'has_anomaly': has_anomaly,
            'severity': severity,
            'description': '; '.join(descriptions) if descriptions else ""
        }
    
    def _compute_trends(
        self,
        current_latency: float,
        current_volume: int,
        current_failure_rate: float
    ) -> Dict[str, Trend]:
        """Compute trends by comparing to historical data."""
        if len(self.historical_signals) < 2:
            return {
                'latency_trend': Trend.UNKNOWN,
                'volume_trend': Trend.UNKNOWN,
                'failure_rate_trend': Trend.UNKNOWN
            }
        
        # Compare to previous window
        prev = self.historical_signals[-1]
        
        # Latency trend
        latency_change = (current_latency - prev.avg_latency_ms) / prev.avg_latency_ms if prev.avg_latency_ms > 0 else 0
        if latency_change > 0.2:  # 20% increase
            latency_trend = Trend.RISING
        elif latency_change < -0.2:  # 20% decrease
            latency_trend = Trend.FALLING
        else:
            latency_trend = Trend.STABLE
        
        # Volume trend
        volume_change = (current_volume - prev.total_payments) / prev.total_payments if prev.total_payments > 0 else 0
        if volume_change > 0.5:  # 50% increase
            volume_trend = Trend.RISING
        elif volume_change < -0.5:  # 50% decrease
            volume_trend = Trend.FALLING
        else:
            volume_trend = Trend.STABLE
        
        # Failure rate trend
        failure_change = current_failure_rate - prev.overall_failure_rate
        if failure_change > 0.1:  # 10% increase
            failure_rate_trend = Trend.RISING
        elif failure_change < -0.1:  # 10% decrease
            failure_rate_trend = Trend.FALLING
        else:
            failure_rate_trend = Trend.STABLE
        
        return {
            'latency_trend': latency_trend,
            'volume_trend': volume_trend,
            'failure_rate_trend': failure_rate_trend
        }
    
    def _percentile(self, sorted_data: List[float], percentile: int) -> float:
        """Calculate percentile from sorted data."""
        if not sorted_data:
            return 0.0
        
        index = (percentile / 100) * (len(sorted_data) - 1)
        lower = int(index)
        upper = min(lower + 1, len(sorted_data) - 1)
        weight = index - lower
        
        return sorted_data[lower] * (1 - weight) + sorted_data[upper] * weight
    
    def _empty_signals(self, window_duration_seconds: int) -> PaymentSignals:
        """Create empty signals for when no data is available."""
        now = datetime.utcnow()
        return PaymentSignals(
            window_start=now.isoformat(),
            window_end=now.isoformat(),
            window_duration_seconds=window_duration_seconds,
            total_payments=0,
            successful_payments=0,
            failed_payments=0,
            overall_success_rate=0.0,
            overall_failure_rate=0.0
        )

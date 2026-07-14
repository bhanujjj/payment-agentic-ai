"""
Action memory storage.

Stores and retrieves action outcomes for learning.
"""

import json
import logging
from pathlib import Path
from typing import List, Optional, Dict, Any
from datetime import datetime

from agent.learning_models import ActionOutcome, LearningStats, OutcomeClassification


class ActionMemory:
    """
    Stores action outcomes and provides retrieval for learning.
    
    Uses simple JSON file storage.
    """
    
    def __init__(self, storage_path: str = "./data/memory/action_memory.json"):
        """
        Initialize memory.
        
        Args:
            storage_path: Path to JSON storage file
        """
        self.storage_path = Path(storage_path)
        self.memories: List[ActionOutcome] = []
        self.logger = logging.getLogger(__name__)
        
        # Create directory if needed
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)
        
        # SQLite db path resolve
        db_path = str(storage_path)
        if db_path.endswith('.json'):
            db_path = db_path.replace('.json', '.db')
        
        import sqlite3
        self.conn = sqlite3.connect(db_path)
        self._init_db()
        
        # Load existing memories
        self.load()
        
    def _init_db(self):
        cursor = self.conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS action_memories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                context_summary TEXT,
                action TEXT,
                risk_level TEXT,
                pre_success_rate REAL,
                pre_latency_ms REAL,
                pre_retry_count INTEGER,
                pre_error_rate REAL,
                post_success_rate REAL,
                post_latency_ms REAL,
                post_retry_count INTEGER,
                post_error_rate REAL,
                success_rate_delta REAL,
                latency_delta REAL,
                retry_delta INTEGER,
                error_rate_delta REAL,
                outcome TEXT,
                outcome_score REAL,
                timestamp TEXT,
                notes TEXT
            )
        """)
        self.conn.commit()
    
    def add(self, outcome: ActionOutcome):
        """
        Store an action outcome.
        
        Args:
            outcome: ActionOutcome to store
        """
        self.memories.append(outcome)
        try:
            cursor = self.conn.cursor()
            cursor.execute("""
                INSERT INTO action_memories (
                    context_summary, action, risk_level,
                    pre_success_rate, pre_latency_ms, pre_retry_count, pre_error_rate,
                    post_success_rate, post_latency_ms, post_retry_count, post_error_rate,
                    success_rate_delta, latency_delta, retry_delta, error_rate_delta,
                    outcome, outcome_score, timestamp, notes
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                outcome.context_summary, outcome.action, outcome.risk_level,
                outcome.pre_success_rate, outcome.pre_latency_ms, outcome.pre_retry_count, outcome.pre_error_rate,
                outcome.post_success_rate, outcome.post_latency_ms, outcome.post_retry_count, outcome.post_error_rate,
                outcome.success_rate_delta, outcome.latency_delta, outcome.retry_delta, outcome.error_rate_delta,
                outcome.outcome.value, outcome.outcome_score, outcome.timestamp.isoformat(), outcome.notes
            ))
            self.conn.commit()
            self.logger.info(
                f"Stored outcome in SQLite: {outcome.action} → {outcome.outcome.value} "
                f"(score: {outcome.outcome_score:.2f})"
            )
        except Exception as e:
            self.logger.error(f"Failed to save SQLite memory: {e}")
    
    def get_all(self) -> List[ActionOutcome]:
        """Get all stored outcomes."""
        return self.memories.copy()
    
    def get_by_action(self, action: str) -> List[ActionOutcome]:
        """
        Get all outcomes for a specific action.
        
        Args:
            action: Action name
            
        Returns:
            List of outcomes for that action
        """
        return [m for m in self.memories if m.action == action]
    
    def get_similar(
        self,
        context_summary: str,
        action: str,
        max_results: int = 5
    ) -> List[ActionOutcome]:
        """
        Get similar past outcomes.
        
        Simple similarity: same action + keyword overlap in context.
        
        Args:
            context_summary: Current context description
            action: Action being considered
            max_results: Max number of results
            
        Returns:
            List of similar outcomes (most recent first)
        """
        # Get outcomes for this action
        action_outcomes = self.get_by_action(action)
        
        if not action_outcomes:
            return []
        
        # Simple keyword-based similarity
        context_keywords = set(context_summary.lower().split())
        
        # Score by keyword overlap
        scored = []
        for outcome in action_outcomes:
            outcome_keywords = set(outcome.context_summary.lower().split())
            overlap = len(context_keywords & outcome_keywords)
            scored.append((overlap, outcome))
        
        # Sort by overlap (descending), then by recency
        scored.sort(key=lambda x: (x[0], x[1].timestamp), reverse=True)
        
        # Return top results
        return [outcome for _, outcome in scored[:max_results]]
    
    def get_action_stats(self, action: str) -> Optional[LearningStats]:
        """
        Get statistics for an action.
        
        Args:
            action: Action name
            
        Returns:
            LearningStats or None if no data
        """
        outcomes = self.get_by_action(action)
        
        if not outcomes:
            return None
        
        success_count = sum(1 for o in outcomes if o.outcome == OutcomeClassification.SUCCESS)
        neutral_count = sum(1 for o in outcomes if o.outcome == OutcomeClassification.NEUTRAL)
        failure_count = sum(1 for o in outcomes if o.outcome == OutcomeClassification.FAILURE)
        
        avg_score = sum(o.outcome_score for o in outcomes) / len(outcomes)
        success_rate = success_count / len(outcomes) if outcomes else 0.0
        
        return LearningStats(
            action=action,
            total_observations=len(outcomes),
            success_count=success_count,
            neutral_count=neutral_count,
            failure_count=failure_count,
            avg_outcome_score=avg_score,
            success_rate=success_rate
        )
    
    def save(self):
        """No-op for SQLite since add() performs SQL persistence."""
        pass
    
    def load(self):
        """Load memories from SQLite database."""
        try:
            cursor = self.conn.cursor()
            cursor.execute("SELECT * FROM action_memories")
            rows = cursor.fetchall()
            
            self.memories = []
            for r in rows:
                from datetime import datetime
                outcome = ActionOutcome(
                    context_summary=r[1],
                    action=r[2],
                    risk_level=r[3],
                    pre_success_rate=r[4],
                    pre_latency_ms=r[5],
                    pre_retry_count=r[6],
                    pre_error_rate=r[7],
                    post_success_rate=r[8],
                    post_latency_ms=r[9],
                    post_retry_count=r[10],
                    post_error_rate=r[11],
                    success_rate_delta=r[12],
                    latency_delta=r[13],
                    retry_delta=r[14],
                    error_rate_delta=r[15],
                    outcome=OutcomeClassification(r[16]),
                    outcome_score=r[17],
                    timestamp=datetime.fromisoformat(r[18]),
                    notes=r[19]
                )
                self.memories.append(outcome)
            self.logger.info(f"Loaded {len(self.memories)} memories from SQLite")
        except Exception as e:
            self.logger.error(f"Failed to load SQLite memories: {e}")
            self.memories = []
    
    def clear(self):
        """Clear all memories from SQLite database."""
        self.memories = []
        try:
            cursor = self.conn.cursor()
            cursor.execute("DELETE FROM action_memories")
            self.conn.commit()
            self.logger.info("Cleared all memories from SQLite")
        except Exception as e:
            self.logger.error(f"Failed to clear SQLite memories: {e}")
            
    def __del__(self):
        if hasattr(self, 'conn') and self.conn:
            try:
                self.conn.close()
            except Exception:
                pass
    
    def get_summary(self) -> Dict[str, Any]:
        """Get summary statistics."""
        if not self.memories:
            return {'total': 0}
        
        by_action = {}
        for memory in self.memories:
            if memory.action not in by_action:
                by_action[memory.action] = []
            by_action[memory.action].append(memory)
        
        return {
            'total': len(self.memories),
            'by_action': {
                action: {
                    'count': len(outcomes),
                    'success': sum(1 for o in outcomes if o.outcome == OutcomeClassification.SUCCESS),
                    'neutral': sum(1 for o in outcomes if o.outcome == OutcomeClassification.NEUTRAL),
                    'failure': sum(1 for o in outcomes if o.outcome == OutcomeClassification.FAILURE),
                }
                for action, outcomes in by_action.items()
            }
        }

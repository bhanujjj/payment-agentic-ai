"""
Reasoner component - LLM-based reasoning about payment signals.

This is the agent's "thinking" layer. It interprets signals,
forms hypotheses, and reasons under uncertainty using an LLM.

IMPORTANT: This layer does NOT make decisions or take actions.
It only provides reasoning and interpretation.
"""

import logging
import json
import os
from typing import Dict, Any, Optional

import google.generativeai as genai

from agent.signals import PaymentSignals
from agent.reasoning_models import ReasoningResult


class Reasoner:
    """
    Reasons about payment events and failures using LLM.
    
    This component uses Gemini to understand complex patterns and uncertainties
    that are difficult to capture with rules.
    
    CRITICAL: This is pure cognition - no decisions, no actions.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize reasoner with Gemini API.
        
        Args:
            config: Configuration dictionary with:
                - gemini_api_key: Gemini API key (or from env)
                - gemini_model: Model name (default: gemini-2.0-flash-exp)
                - temperature: Sampling temperature (default: 0.3)
                - max_tokens: Max output tokens (default: 1000)
        """
        self.config = config or {}
        self.logger = logging.getLogger(__name__)
        
        # Get API key
        api_key = self.config.get('gemini_api_key') or os.getenv('GEMINI_API_KEY')
        if not api_key:
            self.logger.warning("No Gemini API key found. Reasoning will use fallback mode.")
            self.llm_client = None
        else:
            # Configure Gemini
            genai.configure(api_key=api_key)
            
            # Initialize model
            model_name = self.config.get('gemini_model', 'gemini-2.5-flash')
            self.llm_client = genai.GenerativeModel(model_name)
            
            self.logger.info(f"Initialized Gemini reasoner with model: {model_name}")
        
        # Generation config
        self.temperature = self.config.get('temperature', 0.3)
        self.max_tokens = self.config.get('max_tokens', 2000)  # Increased for complete JSON
    
    async def reason(self, signals: PaymentSignals) -> ReasoningResult:
        """
        Reason about the payment signals.
        
        Uses DETERMINISTIC logic for classification and confidence.
        Uses Gemini ONLY for human-readable explanation (optional).
        
        Args:
            signals: Aggregated payment signals from metrics engine
            
        Returns:
            Structured reasoning result with hypotheses and explanations
        """
        self.logger.info("Starting reasoning process")
        
        # STEP 1: Deterministic classification and confidence (NO LLM)
        reasoning = self._deterministic_reasoning(signals)
        
        # STEP 2: Try to get human-readable explanation from Gemini (optional)
        if self.llm_client is not None:
            try:
                explanation = await self._get_llm_explanation(signals, reasoning)
                reasoning.explanation = explanation
                self.logger.info("✅ Got LLM explanation")
            except Exception as e:
                self.logger.warning(f"LLM explanation failed: {e}. Using default.")
                # Keep the default explanation from deterministic reasoning
        
        self.logger.info(f"Reasoning complete. Top hypothesis: {reasoning.get_top_hypothesis()}")
        return reasoning
    
    async def _get_llm_explanation(
        self,
        signals: PaymentSignals,
        reasoning: ReasoningResult
    ) -> str:
        """
        Get human-readable explanation from Gemini.
        
        Gemini returns PLAIN TEXT ONLY - no JSON, no structure.
        This is used for logs, dashboards, and debugging.
        
        Args:
            signals: Payment signals
            reasoning: Deterministic reasoning result
            
        Returns:
            Plain text explanation (1-2 sentences)
        """
        # Get top hypothesis
        top_hyp = reasoning.get_top_hypothesis()
        if not top_hyp:
            return reasoning.explanation
        
        hypothesis_name, confidence = top_hyp
        
        # Build simple prompt for plain text explanation
        prompt = f"""Explain this payment system issue in 1-2 clear sentences for an operations dashboard.

Detected Issue: {hypothesis_name}
Confidence: {confidence:.0%}
Success Rate: {signals.overall_success_rate:.1%}
Degraded Banks: {signals.degraded_banks if signals.degraded_banks else 'None'}
Avg Latency: {signals.avg_latency_ms:.0f}ms

Write a brief, clear explanation for the ops team. Plain text only, no formatting."""
        
        # Call Gemini
        response = self.llm_client.generate_content(
            prompt,
            generation_config=genai.types.GenerationConfig(
                temperature=0.3,
                max_output_tokens=150,  # Short response
            )
        )
        
        # Return plain text (no parsing needed!)
        explanation = response.text.strip()
        
        # Fallback if response is too long or empty
        if not explanation or len(explanation) > 500:
            return reasoning.explanation
        
        return explanation
    

    
    def _deterministic_reasoning(self, signals: PaymentSignals) -> ReasoningResult:
        """
        Deterministic reasoning based on payment signals.
        
        This is the PRIMARY reasoning method - uses rule-based logic
        for classification and confidence calculation.
        
        Args:
            signals: Payment signals
            
        Returns:
            Basic reasoning result
        """
        hypotheses = {}
        assumptions = []
        uncertainty = []
        explanation_parts = []
        
        # Check for normal operation
        if signals.overall_success_rate > 0.95 and not signals.has_anomaly:
            hypotheses["normal_operation"] = 0.9
            explanation_parts.append("System appears to be operating normally.")
        
        # Check for bank issues
        if signals.degraded_banks:
            # Find the worst performing bank's failure rate
            max_bank_fail = max(signals.bank_failure_rates.values()) if signals.bank_failure_rates else 0.0
            
            if len(signals.degraded_banks) > 2:
                # Systemic issue affecting multiple banks
                hypotheses["network_issues"] = 0.75
                explanation_parts.append("Systemic failure across multiple providers suggests network or load issues.")
                assumptions.append("Broad failure is network or load related")
            elif max_bank_fail > 0.6:
                hypotheses["bank_outage"] = 0.85
                explanation_parts.append(f"Critical: Outage detected on bank(s): {', '.join(signals.degraded_banks)}.")
                assumptions.append("Outage on specific bank")
            else:
                hypotheses["bank_degradation"] = 0.8
                explanation_parts.append(f"Detected degraded banks: {', '.join(signals.degraded_banks)}.")
                assumptions.append("Bank degradation is the primary cause")
        
        # Check for high failure rate
        if signals.overall_failure_rate > 0.5 and "bank_outage" not in hypotheses:
            hypotheses["bank_outage"] = 0.7
            explanation_parts.append("Very high failure rate suggests possible outage.")
        
        # Check for latency issues
        if signals.p95_latency_ms > 1000 and "network_issues" not in hypotheses:
            hypotheses["network_issues"] = 0.6
            explanation_parts.append("High latency detected.")
        
        # Check for retry storm
        if signals.total_retries > signals.total_payments * 0.3:
            hypotheses["retry_storm"] = 0.85
            explanation_parts.append("High retry rate detected, indicating a retry storm.")
        
        # Check retry effectiveness
        if signals.retry_effectiveness < -0.2:
            uncertainty.append("Retries don't seem to be helping")
        
        # Default explanation
        if not explanation_parts:
            explanation_parts.append("Insufficient data for detailed analysis.")
            uncertainty.append("Limited signal data")
        
        # Calculate overall confidence
        if hypotheses:
            overall_confidence = max(hypotheses.values()) * 0.7  # Lower for fallback
        else:
            overall_confidence = 0.3
        
        return ReasoningResult(
            hypotheses=hypotheses,
            explanation=" ".join(explanation_parts),
            assumptions=assumptions,
            uncertainty=uncertainty,
            overall_confidence=overall_confidence,
            raw_response="[Fallback reasoning - no LLM]"
        )
